from django.db import models
from apps.users.models import User

class AppFeedback(models.Model):
    TYPES = [('bug','Bug'),('feature_request','Feature Request'),('general','General')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=30, choices=TYPES, default='general')
    message = models.TextField()
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        app_label = 'feedback'
