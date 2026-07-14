from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import School
from .otp import OTPError, confirm_code, issue_code
from .serializers import RegisterSerializer, SchoolSerializer, UserSerializer
from .whatsapp import WhatsAppError, send_verification_code


class SchoolListView(generics.ListAPIView):
    """All institutions, optionally narrowed by ?type=, ?state= or ?search=."""

    serializer_class = SchoolSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    search_fields = ["name", "town__name", "town__state__name"]

    def get_queryset(self):
        qs = School.objects.select_related("town__state")
        institution_type = self.request.query_params.get("type")
        state = self.request.query_params.get("state")
        if institution_type:
            qs = qs.filter(institution_type=institution_type)
        if state:
            qs = qs.filter(town__state__name__iexact=state)
        return qs


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Kick off WhatsApp verification right away; delivery problems are
        # not fatal — the user can request a resend from the verify screen.
        try:
            send_verification_code(user.phone, issue_code(user))
        except (OTPError, WhatsAppError):
            pass
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutView(APIView):
    """Blacklist the presented refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except KeyError:
            return Response(
                {"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class RequestPhoneCodeView(APIView):
    """Send (or resend) a verification code to the user's WhatsApp number."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        user = request.user
        if user.is_phone_verified:
            return Response({"detail": "Your number is already verified."})
        if not user.phone:
            return Response(
                {"detail": "Add a WhatsApp number to your profile first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            send_verification_code(user.phone, issue_code(user))
        except OTPError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except WhatsAppError:
            return Response(
                {"detail": "We couldn't reach WhatsApp. Try again shortly."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"detail": "Code sent. Check your WhatsApp."})


class ConfirmPhoneCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    def post(self, request):
        try:
            confirm_code(request.user, request.data.get("code"))
        except OTPError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "WhatsApp number verified.", "is_phone_verified": True})


class MeView(generics.RetrieveUpdateAPIView):
    """Profile of the authenticated user; PATCH updates location, school, names."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
