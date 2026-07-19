from django.urls import path
from apps.menu.views import MoodListView

urlpatterns = [
    path('', MoodListView.as_view()),
]
