"""
ASGI config for moodbite_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import dotenv
from django.core.asgi import get_asgi_application

# Load environment variables from the root .env
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(root_dir, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moodbite_backend.settings')

# Initialize Django ASGI application early to set up settings/models
django_asgi_app = get_asgi_application()

# Import the websocket handler after initializing Django
from apps.voice_ai.websocket_handler import handle_voice_websocket

async def application(scope, receive, send):
    if scope['type'] == 'websocket' and scope['path'] == '/ws/voice/':
        await handle_voice_websocket(scope, receive, send)
    else:
        await django_asgi_app(scope, receive, send)
