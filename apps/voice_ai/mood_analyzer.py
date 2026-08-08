"""
MoodBite Mood Analyzer — rule-based NLP
Detects mood, intent, and preferences from user text.
Production: swap mock_transcribe() with Google Cloud Speech-to-Text API.
"""
import random

MOOD_KEYWORDS = {
    'happy':        ['happy', 'joy', 'great', 'wonderful', 'love', 'amazing', 'fantastic', 'good', 'cheerful', 'glad'],
    'sad':          ['sad', 'down', 'unhappy', 'depressed', 'lonely', 'upset', 'crying', 'blue', 'miserable', 'gloomy'],
    'stressed':     ['stressed', 'anxious', 'worried', 'pressure', 'overwhelmed', 'tense', 'nervous', 'panic', 'busy', 'deadline'],
    'tired':        ['tired', 'exhausted', 'sleepy', 'fatigue', 'drained', 'low energy', 'worn out', 'lazy', 'sluggish'],
    'excited':      ['excited', 'thrilled', 'pumped', 'enthusiastic', 'hyped', 'motivated', 'psyched', 'charged'],
    'anxious':      ['anxious', 'worried', 'nervous', 'apprehensive', 'uneasy', 'restless', 'fidgety', 'jittery'],
    'romantic':     ['romantic', 'love', 'date', 'special', 'beautiful', 'candlelight', 'partner', 'anniversary'],
    'energetic':    ['energetic', 'active', 'workout', 'gym', 'run', 'exercise', 'fit', 'power', 'strong', 'training', 'cardio'],
    'bored':        ['bored', 'nothing to do', 'monotonous', 'dull', 'restless', 'uneventful', 'same old'],
    'celebratory':  ['celebrate', 'party', 'birthday', 'anniversary', 'achievement', 'success', 'promotion', 'won', 'victory', 'festive'],
    'soothing':     ['calm', 'relax', 'soothe', 'soothing', 'peaceful', 'gentle', 'quiet', 'serene', 'zen', 'unwind', 'chill', 'tranquil'],
    'healthy':      ['healthy', 'nutritious', 'clean eating', 'diet', 'detox', 'fresh', 'organic', 'wholesome', 'balanced', 'nourish', 'light', 'greens'],
    'indulgent':    ['indulge', 'treat', 'cheat day', 'dessert', 'sweet', 'rich', 'splurge', 'craving', 'sinful'],
    'focused':      ['focused', 'concentrate', 'study', 'work', 'productive', 'sharp', 'brain', 'alert'],
}

INTENT_KEYWORDS = {
    'comfort_food':  ['comfort', 'warm', 'cozy', 'soothing', 'filling', 'homely'],
    'healthy_quick': ['healthy', 'light', 'nutritious', 'fresh', 'diet', 'fit', 'salad', 'low cal', 'detox'],
    'indulgent':     ['indulge', 'treat', 'cheat', 'dessert', 'sweet', 'rich', 'splurge'],
    'quick':         ['quick', 'fast', 'hurry', 'instant', 'speed'],
    'spicy':         ['spicy', 'hot', 'fiery', 'chilli', 'peppery'],
    'protein':       ['protein', 'gym', 'muscle', 'gains', 'workout', 'high protein'],
    'romantic':      ['date', 'special', 'romantic', 'anniversary', 'elegant'],
}

MOOD_EMOJIS = {
    'happy': '😊', 'sad': '😢', 'stressed': '😰', 'tired': '😴',
    'excited': '🤩', 'anxious': '😟', 'romantic': '❤️', 'energetic': '💪',
    'bored': '😑', 'celebratory': '🎉', 'soothing': '🧘', 'healthy': '🥗',
    'indulgent': '🍫', 'focused': '🎯',
}


def analyze_mood(text: str) -> dict:
    t = text.lower()
    scores = {}
    for mood, kws in MOOD_KEYWORDS.items():
        s = sum(1 for kw in kws if kw in t)
        if s:
            scores[mood] = s

    secondary = ""
    if not scores:
        primary = 'unknown'
        confidence = 0.0
    else:
        primary = max(scores, key=scores.get)
        total = sum(scores.values())
        confidence = min(0.96, 0.50 + (scores[primary] / max(total, 1)) * 0.45 + random.uniform(0, 0.05))
        if len(scores) > 1:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            secondary = sorted_scores[1][0]

    intent = 'general'
    for name, kws in INTENT_KEYWORDS.items():
        if any(kw in t for kw in kws):
            intent = name
            break

    prefs = []
    if any(w in t for w in ['vegetarian', 'veg', 'no meat']): prefs.append('vegetarian')
    if any(w in t for w in ['spicy', 'hot', 'fiery']): prefs.append('spicy')
    if any(w in t for w in ['healthy', 'light', 'diet']): prefs.append('healthy')
    if any(w in t for w in ['sweet', 'dessert']): prefs.append('sweet')
    if any(w in t for w in ['protein', 'gym', 'workout']): prefs.append('high_protein')

    return {
        "primary_mood": primary,
        "secondary_mood": secondary,
        "confidence": round(confidence, 2),
        "emoji": MOOD_EMOJIS.get(primary, '🍽️'),
        "intent": {
            "type": intent,
            "preferences": prefs,
            "urgency": "urgent" if any(w in t for w in ['quick', 'fast', 'hurry']) else "normal",
        },
    }


def mock_transcribe(audio_file) -> dict:
    """Mock Speech-to-Text. Production: replace with Google Cloud Speech-to-Text or Whisper."""
    samples = [
        "I'm feeling really tired today and want something warm and comforting",
        "I'm happy and excited, let's celebrate with something special!",
        "Feeling stressed, need something light and healthy",
        "I'm bored, surprise me with something interesting to eat",
        "Very hungry after my workout, need high protein food",
        "I want to relax and have something soothing and calming",
        "I need a healthy meal, something fresh and nutritious today",
        "It's my birthday, let's go celebratory with something amazing!",
        "Feeling energetic after my run, want something light but filling",
    ]
    return {
        "text": random.choice(samples),
        "confidence": round(random.uniform(0.88, 0.97), 2),
        "language": "en-US",
    }
