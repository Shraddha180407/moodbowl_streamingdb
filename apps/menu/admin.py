from django.contrib import admin
from .models import MenuItem, Restaurant, MoodCategory

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'cuisine', 'price', 'rating', 'is_vegetarian', 'is_available', 'order_count']
    list_filter = ['category', 'cuisine', 'is_vegetarian', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'price']

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'phone']

@admin.register(MoodCategory)
class MoodAdmin(admin.ModelAdmin):
    list_display = ['mood_id', 'label', 'emoji', 'color']
