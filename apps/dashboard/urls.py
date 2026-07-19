from django.urls import path
from . import views

urlpatterns = [
    path('',          views.serve_dashboard,  name='dashboard'),
    path('stats/',    views.dashboard_stats,  name='dashboard-stats'),
    path('stream/',   views.streaming_events, name='dashboard-stream'),
    path('simulate/', views.simulate_event,   name='dashboard-simulate'),
]
