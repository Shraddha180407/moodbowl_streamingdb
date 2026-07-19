import uuid
from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from .models import VoiceSession
from .mood_analyzer import analyze_mood, mock_transcribe
from apps.recommendations.engine import engine

class ProcessVoiceView(APIView):
    def post(self, request):
        audio = request.FILES.get('audio')
        if not audio:
            return error_response("Audio file required", "MISSING_AUDIO", 400)
        if audio.size > 10 * 1024 * 1024:
            return error_response("File too large (max 10MB)", "FILE_TOO_LARGE", 413)

        transcription = mock_transcribe(audio)  # swap with real API in prod
        mood_data = analyze_mood(transcription['text'])
        session_id = f"session_{uuid.uuid4().hex[:10]}"

        VoiceSession.objects.create(
            user=request.user, session_id=session_id,
            transcription=transcription['text'],
            transcription_confidence=transcription['confidence'],
            primary_mood=mood_data['primary_mood'],
            secondary_mood=mood_data.get('secondary_mood', ''),
            mood_confidence=mood_data['confidence'],
            emoji=mood_data['emoji'],
            intent_type=mood_data['intent']['type'],
            context=request.data.get('context', {}),
        )
        engine.push_event({"type": "voice_session", "mood": mood_data['primary_mood'], "session_id": session_id, "user_id": request.user.id})

        return success_response({
            "transcription": {"text": transcription['text'], "confidence": transcription['confidence'], "language": transcription['language']},
            "mood_analysis": {"primary_mood": mood_data['primary_mood'], "secondary_mood": mood_data['secondary_mood'],
                              "confidence": mood_data['confidence'], "emoji": mood_data['emoji']},
            "intent": mood_data['intent'],
            "session_id": session_id,
        })

class AnalyzeTextView(APIView):
    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return error_response("Text is required", "MISSING_TEXT", 400)
        mood_data = analyze_mood(text)
        session_id = f"session_{uuid.uuid4().hex[:10]}"
        VoiceSession.objects.create(
            user=request.user, session_id=session_id,
            transcription=text, primary_mood=mood_data['primary_mood'],
            mood_confidence=mood_data['confidence'], emoji=mood_data['emoji'],
            intent_type=mood_data['intent']['type'],
        )
        engine.push_event({"type": "text_analysis", "mood": mood_data['primary_mood'], "session_id": session_id})
        return success_response({
            "mood_analysis": {"primary_mood": mood_data['primary_mood'], "confidence": mood_data['confidence'], "emoji": mood_data['emoji']},
            "intent": mood_data['intent'],
            "session_id": session_id,
        })
