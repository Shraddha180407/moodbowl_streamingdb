# 🔗 How Frontend + Backend Connect

The frontend (your React/JS app) and backend (this Django server) are served
**from the same server** — no CORS issues, no separate deploys needed.

```
http://localhost:8000/
        │
        ├── /app/           ← Frontend SPA (templates/app.html + static/)
        │                      All your UI: login, mood picker, menu, cart, orders
        │
        ├── /dashboard/     ← Analytics dashboard (templates/dashboard.html)
        │                      Mood analytics, orders, live stream, ML model
        │
        ├── /api/...        ← REST API (Django)
        │     ├── /api/auth/login/
        │     ├── /api/recommendations/generate/
        │     ├── /api/menu/items/
        │     ├── /api/cart/
        │     ├── /api/orders/create/
        │     └── ... (all endpoints)
        │
        └── /admin/         ← Django admin panel
```

## Why it works without cloning the GitHub repo separately

Your frontend files are already included in this zip:
- `templates/app.html`  — the full SPA shell (all screens: splash, onboarding, login,
                           mood picker, home, explore, cart, profile, tracking)
- `static/js/app.js`    — all frontend logic, API calls, voice recording
- `static/css/app.css`  — all styles

The Django server serves `app.html` at `/app/` using:
```python
path('app/', TemplateView.as_view(template_name='app.html'))
```

And serves the JS/CSS at `/static/` automatically via WhiteNoise.

## How the frontend calls the backend

All API calls in `app.js` use **relative paths**:
```javascript
const API = '/api';
// Example: fetch('/api/auth/login/', {...})
// Example: fetch('/api/recommendations/generate/', {...})
```

Because the frontend is served from the same domain as the backend,
every `fetch('/api/...')` automatically hits your Django server.
No `http://localhost:8000` hardcoded — it works on any host.

## Voice ordering flow

```
1. User clicks mic button in the app
2. Browser Web Speech API transcribes speech locally (no upload needed)
3. Transcript sent to POST /api/ai/analyze-text/ → mood detected
4. Frontend updates currentMood, calls POST /api/recommendations/generate/
5. Mood-matched food shown instantly
6. User adds to cart → places order (mood saved on order)
7. After delivery → user rates → ML model updated automatically
```

## What updates the analytics dashboard

Every user action feeds the dashboard:
- Login / register → user count updates
- Voice/text mood analysis → voice session logged
- Add to cart, place order → order with mood_context saved
- Rate order → streaming ML model updated (engine.pkl saved)
- Dashboard at /dashboard/ shows all this in real time via SSE stream

## If you want to update the frontend

The frontend code is in:
- `templates/app.html` — HTML structure, all view screens
- `static/js/app.js`  — all JavaScript logic
- `static/css/app.css` — all CSS styles

Edit these files directly. No build step needed — it's vanilla JS.
After editing, just refresh the browser. For production, run:
```bash
python manage.py collectstatic
```
