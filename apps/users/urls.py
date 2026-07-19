from django.urls import path
from . import views
urlpatterns = [
    path('profile/', views.ProfileView.as_view()),
    path('profile/update/', views.ProfileUpdateView.as_view()),
    path('preferences/', views.PreferencesView.as_view()),
]
