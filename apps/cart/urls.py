from django.urls import path
from . import views
urlpatterns = [
    path('cart/', views.CartView.as_view()),
    path('cart/add/', views.CartAddView.as_view()),
    path('cart/items/<int:item_id>/', views.CartItemView.as_view()),
    path('cart/clear/', views.CartClearView.as_view()),
]
