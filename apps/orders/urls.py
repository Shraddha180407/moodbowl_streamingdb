from django.urls import path
from . import views
urlpatterns = [
    path('orders/create/', views.CreateOrderView.as_view()),
    path('orders/history/', views.OrderHistoryView.as_view()),
    path('orders/<int:order_id>/', views.OrderDetailView.as_view()),
    path('orders/<int:order_id>/cancel/', views.CancelOrderView.as_view()),
    path('orders/<int:order_id>/reorder/', views.ReorderView.as_view()),
    path('orders/<int:order_id>/rate/', views.RateOrderView.as_view()),
]
