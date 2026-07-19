from rest_framework import serializers
from .models import User, UserPreference

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['dietary', 'allergies', 'favorite_cuisines', 'spice_level', 'budget_range']

class UserSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'profile_image', 'preferences', 'created_at']
