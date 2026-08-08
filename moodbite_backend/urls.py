from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView


def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "services": {
            "database": "ok",
            "speech_api": "mock — swap mock_transcribe() for Google/Whisper in production",
            "ml_model": "streaming_ema",
        }
    })


def app_config(request):
    return JsonResponse({"success": True, "data": {
        "app_version": "2.0.0",
        "min_order_amount": 100,
        "delivery_fee": 50,
        "free_delivery_above": 500,
        "currencies": {"symbol": "₹", "code": "INR"},
        "contact": {
            "support_email": "support@moodbite.com",
            "support_phone": "+911234567890",
        },
        "features": {
            "voice_ordering": True,
            "mood_recommendations": True,
            "social_login": False,
            "live_tracking": False,
            "streaming_ml": True,
        },
        "moods": [
            {"id": "happy",       "emoji": "😊", "label": "Happy"},
            {"id": "sad",         "emoji": "😢", "label": "Sad"},
            {"id": "stressed",    "emoji": "😰", "label": "Stressed"},
            {"id": "tired",       "emoji": "😴", "label": "Tired"},
            {"id": "excited",     "emoji": "🤩", "label": "Excited"},
            {"id": "anxious",     "emoji": "😟", "label": "Anxious"},
            {"id": "romantic",    "emoji": "❤️",  "label": "Romantic"},
            {"id": "energetic",   "emoji": "💪", "label": "Energetic"},
            {"id": "bored",       "emoji": "😑", "label": "Bored"},
            {"id": "celebratory", "emoji": "🎉", "label": "Celebratory"},
            {"id": "soothing",    "emoji": "🧘", "label": "Soothing"},
            {"id": "healthy",     "emoji": "🥗", "label": "Healthy"},
            {"id": "indulgent",   "emoji": "🍫", "label": "Indulgent"},
            {"id": "focused",     "emoji": "🎯", "label": "Focused"},
        ]
    }})


def serve_unregister_sw(request):
    js_content = """
    self.addEventListener('install', function(e) {
      self.skipWaiting();
    });
    self.addEventListener('activate', function(e) {
      self.registration.unregister()
        .then(function() {
          return self.clients.matchAll();
        })
        .then(function(clients) {
          clients.forEach(client => {
            try { client.navigate(client.url); } catch(err) {}
          });
        });
    });
    """
    return HttpResponse(js_content, content_type='application/javascript')


urlpatterns = [
    # Clean up old service worker
    path('sw.js', serve_unregister_sw),
    # Root redirect
    path('', lambda r: HttpResponseRedirect('/app/')),
    # Frontend SPA
    path('app/', TemplateView.as_view(template_name='app.html'), name='app'),
    # Analytics dashboard
    path('dashboard/', include('apps.dashboard.urls')),
    # Admin
    path('admin/', admin.site.urls),
    # API — health & config
    path('api/health/', health_check),
    path('api/config/', app_config),
    # API — auth & users
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    # API — voice & mood
    path('api/', include('apps.voice_ai.urls')),
    path('api/moods/', include('apps.voice_ai.mood_urls')),
    # API — recommendations
    path('api/', include('apps.recommendations.urls')),
    # API — menu, cart, orders
    path('api/menu/', include('apps.menu.urls')),
    path('api/', include('apps.cart.urls')),
    path('api/', include('apps.orders.urls')),
    # API — addresses & feedback
    path('api/addresses/', include('apps.addresses.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
