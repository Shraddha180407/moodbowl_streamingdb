from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from .models import AppFeedback

class FeedbackView(APIView):
    def post(self, request):
        if not request.data.get('message'):
            return error_response("Message is required", status_code=400)
        AppFeedback.objects.create(user=request.user,
            type=request.data.get('type','general'),
            message=request.data['message'],
            rating=request.data.get('rating'))
        return success_response(message="Feedback submitted", status_code=201)
