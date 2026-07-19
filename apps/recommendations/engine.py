"""
MoodBite Streaming Recommendation Engine
- Synthetic mood-to-food knowledge base (cold start)
- Online learning via EMA on user ratings
- Self-improves with every review submitted
"""
import pickle, time, random
from pathlib import Path
from collections import defaultdict

MODEL_PATH = Path(__file__).parent.parent.parent / 'ml_models' / 'recommender.pkl'

MOOD_CATEGORY_AFFINITY = {
    'happy':       {'dessert':0.90,'beverage':0.80,'snack':0.75,'main_course':0.65,'starter':0.60,'street_food':0.70},
    'sad':         {'comfort_food':0.95,'dessert':0.88,'main_course':0.72,'beverage':0.65,'breakfast':0.60},
    'stressed':    {'healthy':0.92,'beverage':0.85,'snack':0.68,'main_course':0.50,'breakfast':0.55},
    'tired':       {'comfort_food':0.92,'main_course':0.82,'beverage':0.78,'snack':0.65,'breakfast':0.70},
    'excited':     {'snack':0.90,'dessert':0.85,'starter':0.82,'street_food':0.88,'beverage':0.72},
    'anxious':     {'healthy':0.88,'beverage':0.82,'snack':0.60,'breakfast':0.65},
    'romantic':    {'dessert':0.92,'main_course':0.88,'starter':0.82,'beverage':0.78},
    'energetic':   {'healthy':0.92,'snack':0.85,'breakfast':0.88,'beverage':0.72,'main_course':0.65},
    'bored':       {'snack':0.90,'street_food':0.88,'starter':0.75,'main_course':0.60},
    'celebratory': {'dessert':0.95,'beverage':0.90,'main_course':0.82,'starter':0.78,'snack':0.70},
    'soothing':    {'beverage':0.95,'healthy':0.90,'breakfast':0.80,'comfort_food':0.72,'snack':0.60},
    'healthy':     {'healthy':0.98,'breakfast':0.85,'beverage':0.75,'main_course':0.60,'snack':0.50},
    'indulgent':   {'dessert':0.98,'snack':0.85,'main_course':0.75,'street_food':0.70,'starter':0.65},
    'focused':     {'healthy':0.90,'beverage':0.85,'snack':0.72,'breakfast':0.80},
}

MOOD_CUISINE_AFFINITY = {
    'happy':       {'Italian':0.88,'Mexican':0.82,'Continental':0.72,'Indian':0.70},
    'sad':         {'Indian':0.92,'Italian':0.85,'Continental':0.70,'Chinese':0.68},
    'stressed':    {'Japanese':0.90,'Thai':0.85,'Continental':0.72,'Indian':0.60},
    'tired':       {'Indian':0.90,'Italian':0.82,'Chinese':0.72,'Continental':0.65},
    'excited':     {'Mexican':0.90,'Chinese':0.88,'Thai':0.82,'Indian':0.75},
    'anxious':     {'Japanese':0.88,'Continental':0.82,'Thai':0.72,'Indian':0.60},
    'romantic':    {'Italian':0.95,'Continental':0.88,'Japanese':0.82,'Thai':0.72},
    'energetic':   {'Thai':0.90,'Mexican':0.85,'Indian':0.78,'Continental':0.70},
    'bored':       {'Chinese':0.88,'Mexican':0.85,'Indian':0.82,'Thai':0.75},
    'celebratory': {'Italian':0.90,'Continental':0.88,'Indian':0.82,'Mexican':0.75},
    'soothing':    {'Japanese':0.95,'Thai':0.88,'Continental':0.80,'Indian':0.65},
    'healthy':     {'Continental':0.92,'Japanese':0.88,'Thai':0.82,'Indian':0.65},
    'indulgent':   {'Italian':0.92,'Continental':0.85,'Indian':0.78,'Mexican':0.72},
    'focused':     {'Japanese':0.88,'Continental':0.82,'Thai':0.75,'Indian':0.60},
}

MOOD_REASONS = {
    'happy':       "This joyful dish perfectly matches your celebratory mood!",
    'sad':         "Comfort food to warm your heart and lift your spirits.",
    'stressed':    "Light and nourishing — exactly what you need to unwind.",
    'tired':       "Easy, filling fuel to recharge your energy.",
    'excited':     "A fun, bold dish to match your high energy!",
    'anxious':     "Calming, wholesome food to help ease your mind.",
    'romantic':    "An elegant choice for this special moment.",
    'energetic':   "Power-packed nutrition to fuel your momentum!",
    'bored':       "Something adventurous to break the monotony!",
    'celebratory': "Celebrate in style with this crowd favourite!",
    'soothing':    "A gentle, calming dish to bring you peace and serenity.",
    'healthy':     "Clean, nutritious fuel aligned with your wellness goals.",
    'indulgent':   "You deserve this treat — enjoy every bite guilt-free!",
    'focused':     "Brain-boosting food to keep you sharp and productive.",
}


class StreamingRecommender:
    def __init__(self):
        self.learned_scores = defaultdict(dict)
        self.sample_counts = defaultdict(dict)
        self.total_updates = 0
        self.mood_order_counts = defaultdict(int)
        self.live_events = []

    def _base_score(self, mood, category, cuisine):
        cat = MOOD_CATEGORY_AFFINITY.get(mood, {}).get(category, 0.30)
        cui = MOOD_CUISINE_AFFINITY.get(mood, {}).get(cuisine, 0.30)
        return cat * 0.55 + cui * 0.45

    def score(self, mood, item):
        base = self._base_score(mood, item.category, item.cuisine)
        # Also boost items that have mood_tags matching
        if hasattr(item, 'mood_tags') and mood in (item.mood_tags or []):
            base = min(1.0, base + 0.15)
        n = self.sample_counts[mood].get(item.id, 0)
        if n == 0:
            return base
        learned = self.learned_scores[mood].get(item.id, base * 5) / 5.0
        w = min(n / 15.0, 0.75)
        return (1 - w) * base + w * learned

    def recommend(self, mood, items, top_n=10):
        scored = [
            (item, self.score(mood, item) + random.uniform(-0.015, 0.015))
            for item in items
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def update(self, mood, item_id, rating):
        alpha = 0.12
        old = self.learned_scores[mood].get(item_id, rating)
        self.learned_scores[mood][item_id] = (1 - alpha) * old + alpha * rating
        self.sample_counts[mood][item_id] = self.sample_counts[mood].get(item_id, 0) + 1
        self.total_updates += 1
        self.mood_order_counts[mood] += 1
        self.live_events.append({
            "ts": time.time(), "type": "rating_update",
            "mood": mood, "item_id": item_id, "rating": rating,
            "total_updates": self.total_updates,
        })
        if len(self.live_events) > 2000:
            self.live_events = self.live_events[-1000:]
        self._save()

    def push_event(self, event):
        event["ts"] = time.time()
        self.live_events.append(event)
        if len(self.live_events) > 2000:
            self.live_events = self.live_events[-1000:]

    def stats(self):
        return {
            "total_updates": self.total_updates,
            "moods_with_data": len(self.learned_scores),
            "items_per_mood": {m: len(v) for m, v in self.learned_scores.items()},
            "mood_order_counts": dict(self.mood_order_counts),
        }

    def _save(self):
        try:
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump({
                    'learned_scores': dict(self.learned_scores),
                    'sample_counts': dict(self.sample_counts),
                    'total_updates': self.total_updates,
                    'mood_order_counts': dict(self.mood_order_counts),
                }, f)
        except Exception as e:
            print(f"[Recommender] Save error: {e}")

    def load(self):
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.learned_scores = defaultdict(dict, data.get('learned_scores', {}))
                self.sample_counts = defaultdict(dict, data.get('sample_counts', {}))
                self.total_updates = data.get('total_updates', 0)
                self.mood_order_counts = defaultdict(int, data.get('mood_order_counts', {}))
                print(f"[Recommender] Loaded — {self.total_updates} training samples")
        except Exception as e:
            print(f"[Recommender] Load error: {e}")


engine = StreamingRecommender()
engine.load()
