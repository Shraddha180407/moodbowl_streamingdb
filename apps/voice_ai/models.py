from django.db import models
from apps.users.models import User

class VoiceSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_sessions')
    session_id = models.CharField(max_length=60, unique=True)
    transcription = models.TextField(blank=True)
    transcription_confidence = models.FloatField(default=0)
    language = models.CharField(max_length=10, default='en-US')
    primary_mood = models.CharField(max_length=30, blank=True)
    secondary_mood = models.CharField(max_length=30, blank=True)
    mood_confidence = models.FloatField(default=0)
    emoji = models.CharField(max_length=10, blank=True)
    intent_type = models.CharField(max_length=50, blank=True)
    context = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'voice_ai'

    def __str__(self):
        return f"{self.user} | {self.primary_mood} | {self.session_id}"
