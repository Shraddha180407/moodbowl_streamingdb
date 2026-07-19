from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from .serializers import UserSerializer, UserPreferenceSerializer
from .models import UserPreference

class ProfileView(APIView):
    def get(self, request):
        return success_response(UserSerializer(request.user).data)

class ProfileUpdateView(APIView):
    def put(self, request):
        user = request.user
        for field in ['name', 'phone', 'profile_image']:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return success_response(UserSerializer(user).data, "Profile updated successfully")

class PreferencesView(APIView):
    def put(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Preferences updated")
        return error_response("Validation error", details=serializer.errors)
