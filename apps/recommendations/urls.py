from django.urls import path
from . import views
urlpatterns = [
    path('recommendations/generate/', views.GenerateRecommendationsView.as_view()),
    path('recommendations/popular/', views.PopularByMoodView.as_view()),
    path('recommendations/model-stats/', views.ModelStatsView.as_view()),
]
