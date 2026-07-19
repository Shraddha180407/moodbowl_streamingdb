from django.urls import path
from . import views
urlpatterns = [
    path('voice/process/', views.ProcessVoiceView.as_view()),
    path('ai/analyze-text/', views.AnalyzeTextView.as_view()),
]
