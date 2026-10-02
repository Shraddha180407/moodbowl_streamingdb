import uuid, random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseRefreshView
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, UserPreference, OTPRecord
from apps.users.serializers import UserSerializer

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}

def ok(data=None, message="", status=200, **kwargs):
    p = {"success": True}
    if message: p["message"] = message
    if data is not None: p["data"] = data
    p.update(kwargs)
    return Response(p, status=status)

def err(msg, code="ERROR", status=400, details=None):
    p = {"success": False, "error": {"code": code, "message": msg}}
    if details: p["error"]["details"] = details
    return Response(p, status=status)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data
        if not data.get('email') or not data.get('password'):
            return err("Email and password are required", "VALIDATION_ERROR", 422)
        if User.objects.filter(email=data['email']).exists():
            return err("Email already exists", "EMAIL_EXISTS", 400)
        user = User.objects.create_user(
            email=data['email'], password=data['password'],
            name=data.get('name', ''), phone=data.get('phone', '')
        )
        UserPreference.objects.create(user=user)
        return Response({"success": True, "message": "User registered successfully",
            "data": {"user_id": user.id, "email": user.email, "name": user.name,
                     "phone": user.phone, "is_staff": user.is_staff},
            "token": get_tokens(user)}, status=201)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        user = authenticate(email=request.data.get('email', ''), password=request.data.get('password', ''))
        if not user:
            return err("Invalid credentials", "INVALID_CREDENTIALS", 401)
        return Response({"success": True, "message": "Login successful",
            "data": {"user_id": user.id, "email": user.email, "name": user.name,
                     "phone": user.phone, "profile_image": user.profile_image,
                     "is_staff": user.is_staff},
            "token": get_tokens(user)})

class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh', '')).blacklist()
        except Exception:
            pass
        return ok(message="Logged out successfully")

class TokenRefreshView(BaseRefreshView):
    permission_classes = [AllowAny]

class SendOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone = request.data.get('phone', '')
        if not phone:
            return err("Phone number required", status=400)
        otp = str(random.randint(100000, 999999))
        otp_id = f"otp_{uuid.uuid4().hex[:12]}"
        OTPRecord.objects.create(phone=phone, otp=otp, otp_id=otp_id,
            expires_at=timezone.now() + timedelta(minutes=5))
        # In production: send SMS via Twilio/MSG91
        return Response({"success": True, "message": "OTP sent successfully",
            "data": {"otp_id": otp_id, "expires_in": 300, "_dev_otp": otp}})

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone = request.data.get('phone')
        otp_val = request.data.get('otp')
        otp_id = request.data.get('otp_id')
        try:
            record = OTPRecord.objects.get(phone=phone, otp=otp_val, otp_id=otp_id, is_verified=False)
        except OTPRecord.DoesNotExist:
            return err("Invalid OTP", "INVALID_OTP", 400)
        if record.expires_at < timezone.now():
            return err("OTP has expired", "OTP_EXPIRED", 400)
        record.is_verified = True
        record.save()
        user, _ = User.objects.get_or_create(
            phone=phone,
            defaults={'email': f'phone_{phone.replace("+","")}@moodbite.com', 'name': 'MoodBite User'}
        )
        user.is_phone_verified = True
        user.save()
        return Response({"success": True, "message": "Phone verified", "token": get_tokens(user)})

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # In production: verify with google-auth library
        # google.oauth2.id_token.verify_oauth2_token(id_token, requests.Request(), CLIENT_ID)
        id_token = request.data.get('id_token', '')
        if not id_token:
            return err("id_token required", status=400)
        # Mock: extract email from token (prod: decode properly)
        mock_email = "google_user@gmail.com"
        mock_name = "Google User"
        user, is_new = User.objects.get_or_create(
            email=mock_email, defaults={'name': mock_name}
        )
        if is_new:
            UserPreference.objects.create(user=user)
        return Response({"success": True, "message": "Login successful",
            "data": {"user_id": user.id, "email": user.email, "name": user.name, "is_new_user": is_new},
            "token": get_tokens(user)})
