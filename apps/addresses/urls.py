from django.urls import path
from . import views
urlpatterns = [
    path('', views.AddressListView.as_view()),
    path('<int:addr_id>/', views.AddressDetailView.as_view()),
]
