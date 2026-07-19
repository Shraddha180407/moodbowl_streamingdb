from django.urls import path
from . import views
urlpatterns = [
    path('items/', views.MenuListView.as_view()),
    path('items/<int:item_id>/', views.MenuItemDetailView.as_view()),
    path('search/', views.MenuSearchView.as_view()),
]
