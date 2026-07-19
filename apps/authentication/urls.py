from django.urls import path
from . import views
urlpatterns = [
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('refresh-token/', views.TokenRefreshView.as_view()),
    path('send-otp/', views.SendOTPView.as_view()),
    path('verify-otp/', views.VerifyOTPView.as_view()),
    path('google-login/', views.GoogleLoginView.as_view()),
]
