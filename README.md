# 🍽️ MoodBite Backend — Complete Setup Guide

A mood-aware food ordering backend with voice ordering, streaming ML recommendations, and a live analytics dashboard.

---

## 🚀 Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
python manage.py migrate

# 3. Seed with synthetic data (14 moods, 47 items, 20 users, 300 orders)
python manage.py seed_data

# 4. (Optional) Create admin user
python manage.py createsuperuser

# 5. Start the server
python manage.py runserver
```

### URLs
| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Redirects to frontend app |
| `http://localhost:8000/app/` | Frontend SPA |
| `http://localhost:8000/dashboard/` | 📊 **Analytics Dashboard** |
| `http://localhost:8000/admin/` | Django Admin |
| `http://localhost:8000/api/health/` | Health check |
| `http://localhost:8000/api/config/` | App config + all 14 moods |

### Demo Login
```
Email:    user1@moodbite.demo
Password: demo1234
```

---

## 🌐 Deploy to Railway (Recommended — Free Tier)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects Python and uses `railway.toml`
5. The app migrates, seeds, and starts automatically
6. Your analytics dashboard URL: `https://your-app.railway.app/dashboard/`

**Optional env vars to set in Railway dashboard:**
```
DEBUG=False
DJANGO_SECRET_KEY=your-random-secret-key-here
ALLOWED_HOSTS=your-app.railway.app
```

---

## 🌐 Deploy to Render (Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect repo, Render auto-detects `render.yaml`
4. Dashboard URL: `https://your-app.onrender.com/dashboard/`

---

## 📡 All API Endpoints

### Auth
```
POST /api/auth/register/          Register new user
POST /api/auth/login/             Login → returns JWT tokens
POST /api/auth/logout/            Logout (blacklists refresh token)
POST /api/auth/token/refresh/     Refresh access token
POST /api/auth/send-otp/          Send OTP to phone (mock — logs OTP in dev)
POST /api/auth/verify-otp/        Verify OTP
```

### Users
```
GET  /api/users/profile/          Get current user profile
PUT  /api/users/profile/update/   Update name, phone, profile_image
PUT  /api/users/preferences/      Update dietary prefs, allergies, cuisines
```

### Voice & Mood
```
POST /api/voice/process/          Upload audio → transcribe → mood → recommendations
                                  Body: multipart/form-data { audio: <file> }
                                  Response: { transcription, mood_analysis, intent, session_id }

POST /api/voice/analyze-text/     Text → mood analysis (no audio needed)
                                  Body: { text: "I feel tired and want comfort food" }
                                  Response: { mood_analysis: { primary_mood, confidence, emoji }, intent }

GET  /api/moods/                  List all 14 mood categories with emoji + color
```

### Recommendations
```
POST /api/recommendations/generate/   Get mood-based food recommendations
     Body: {
       "mood": "soothing",
       "filters": { "vegetarian": true, "max_price": 400, "cuisine": ["Indian"] }
     }
     Response: { recommendations: [...], personalization_score }

GET  /api/recommendations/popular/?mood=energetic   Top items for a mood
GET  /api/recommendations/model-stats/              ML model training stats
```

### Menu
```
GET  /api/menu/items/             List menu (filters: category, cuisine, vegetarian, price, sort_by)
GET  /api/menu/items/<id>/        Menu item detail
POST /api/menu/search/            Full-text search with filters
```

### Cart
```
GET    /api/cart/                 View cart (with totals)
POST   /api/cart/add/             Add item { item_id, quantity, customizations }
PUT    /api/cart/items/<id>/      Update quantity
DELETE /api/cart/items/<id>/      Remove item
DELETE /api/cart/clear/           Clear cart
```

### Orders
```
POST /api/orders/create/          Place order from cart
     Body: {
       delivery_address: {...},
       payment_method: "upi",
       mood_context: { detected_mood: "celebratory", recommended_mood: "celebratory" },
       coupon_code: "MOOD20"
     }

GET  /api/orders/history/         Order history (filter: status, page, limit)
GET  /api/orders/<id>/            Order detail + status history
POST /api/orders/<id>/cancel/     Cancel order
POST /api/orders/<id>/reorder/    Re-add order items to cart
POST /api/orders/<id>/rate/       Rate order → triggers ML model update
     Body: { rating: 5, food_rating: 4, delivery_rating: 5, review: "Amazing!" }
```

### Addresses
```
GET    /api/addresses/            List saved addresses
POST   /api/addresses/            Add address
DELETE /api/addresses/<id>/       Delete address
```

### Feedback
```
POST /api/feedback/               Submit app feedback { type, message, rating }
```

### Dashboard (Analytics)
```
GET /dashboard/           Analytics dashboard HTML page
GET /dashboard/stats/     All analytics JSON (overview, moods, orders, ML stats)
GET /dashboard/stream/    Server-Sent Events (live stream of orders/ML updates)
GET /dashboard/simulate/  Simulate a random order for demo purposes
```

---

## 🎙️ Voice Ordering — How It Works

```
User speaks → Audio uploaded to POST /api/voice/process/
           → mock_transcribe() converts to text
              (Swap with Google Cloud Speech-to-Text or Whisper for production)
           → analyze_mood() detects mood from text using keyword NLP
           → Returns mood + intent + session_id
           → Frontend calls POST /api/recommendations/generate/ with detected mood
           → User sees mood-personalized menu
           → User adds to cart → places order (mood_context stored on order)
           → After delivery, user rates → engine.update() trains the model
```

**To use real Speech-to-Text**, open `apps/voice_ai/mood_analyzer.py` and replace `mock_transcribe()`:
```python
# Google Cloud Speech-to-Text
from google.cloud import speech
def mock_transcribe(audio_file) -> dict:
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_file.read())
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, sample_rate_hertz=48000, language_code="en-IN")
    response = client.recognize(config=config, audio=audio)
    text = response.results[0].alternatives[0].transcript
    confidence = response.results[0].alternatives[0].confidence
    return {"text": text, "confidence": confidence, "language": "en-IN"}
```

---

## 🧠 Streaming ML Model — How It Works

The recommender (`apps/recommendations/engine.py`) uses **Exponential Moving Average** online learning:

```
Cold Start (first users):
  score(mood, item) = 0.55 × mood_category_affinity + 0.45 × mood_cuisine_affinity
  14 moods × 9 categories × 7 cuisines = synthetic knowledge base

After User Rating:
  new_score = 0.88 × old_score + 0.12 × user_rating    (alpha=0.12)
  learned_weight grows to max 75% at 15+ samples per mood-item pair

Live Dashboard:
  Every rating triggers engine.update() → saved to recommender.pkl
  SSE stream at /dashboard/stream/ shows updates in real time
```

**The model persists** to `ml_models/recommender.pkl` on every update — so it survives server restarts.

---

## 📊 Analytics Dashboard — Key Features

- **Dashboard Overview**: 30-day orders + revenue trend, order status donut, cuisine breakdown, payment methods, hourly heatmap
- **Mood Analytics**: 
  - Toggle between **"Mood Ordered Under"** (user's emotional state) and **"Mood Recommended From"** (AI's filter)
  - Click any mood card to see which food categories it drives
  - Side-by-side panels: recent orders per mood × both mood types
- **Orders Tab**: Full orders table showing both mood columns per order
- **Live Stream**: Real-time SSE feed of orders, ratings, ML updates, voice sessions
- **ML Model Tab**: Training samples, items learned per mood, EMA visualisation
- **Top Items**: Most ordered dishes with ratings

---

## 😊 14 Supported Moods

| Mood | Emoji | Food Affinity |
|------|-------|--------------|
| Happy | 😊 | Desserts, beverages, street food |
| Sad | 😢 | Comfort food, desserts |
| Stressed | 😰 | Healthy, beverages, light food |
| Tired | 😴 | Comfort food, main course |
| Excited | 🤩 | Snacks, desserts, street food |
| Anxious | 😟 | Healthy, beverages, breakfast |
| Romantic | ❤️ | Desserts, main course, starters |
| **Energetic** | 💪 | Healthy, breakfast, snacks |
| Bored | 😑 | Snacks, street food, starters |
| **Celebratory** | 🎉 | Desserts, beverages, main course |
| **Soothing** | 🧘 | Beverages, healthy, breakfast |
| **Healthy** | 🥗 | Healthy, breakfast, beverages |
| **Indulgent** | 🍫 | Desserts, snacks, main course |
| Focused | 🎯 | Healthy, beverages, breakfast |

*(Bold = newly added moods)*

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | insecure dev key | **Change in production!** |
| `DEBUG` | `True` | Set `False` in production |
| `ALLOWED_HOSTS` | `*` | Set to your domain in production |
| `DATABASE_URL` | SQLite | Set to `postgres://...` for PostgreSQL |

---

## 🗂️ Project Structure

```
moodbite_backend/         ← Django project config
  settings.py             ← Config (reads env vars for production)
  urls.py                 ← All URL routing
  utils.py                ← success_response / error_response helpers

apps/
  authentication/         ← JWT login, register, OTP
  users/                  ← Profile, preferences
  voice_ai/               ← Audio processing, mood analysis, NLP
    mood_analyzer.py      ← Keyword NLP (swap for real STT here)
  menu/                   ← Menu items, restaurants, mood categories
    management/commands/seed_data.py  ← Synthetic data seeder
  recommendations/        ← Mood → food recommendations
    engine.py             ← Streaming EMA ML model
  cart/                   ← Shopping cart
  orders/                 ← Order lifecycle + ratings (triggers ML)
  addresses/              ← Saved delivery addresses
  feedback/               ← App feedback
  dashboard/              ← Analytics dashboard + SSE stream

templates/
  dashboard.html          ← Full analytics dashboard (Chart.js)
  app.html                ← Frontend SPA shell (served from GitHub)

ml_models/
  recommender.pkl         ← Persisted ML model (auto-updated on ratings)
```
