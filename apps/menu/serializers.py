from rest_framework import serializers
from .models import MenuItem, Restaurant, MoodCategory

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'rating', 'phone']

class MenuItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id','name','description','price','image','category','cuisine',
                  'rating','is_vegetarian','is_available','preparation_time','mood_tags','order_count']

class MenuItemDetailSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)
    nutritional_info = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id','name','description','price','image','category','cuisine',
                  'rating','reviews_count','is_vegetarian','is_available','preparation_time',
                  'nutritional_info','ingredients','customizations','mood_tags','restaurant']

    def get_nutritional_info(self, obj):
        return {"calories": obj.calories, "protein": obj.protein, "carbs": obj.carbs, "fat": obj.fat}

class MoodCategorySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='mood_id')
    class Meta:
        model = MoodCategory
        fields = ['id', 'label', 'emoji', 'color', 'description']
