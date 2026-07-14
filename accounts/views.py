from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .google import GoogleAuthError, verify_id_token
from .models import School, User
from .serializers import RegisterSerializer, SchoolSerializer, UserSerializer

# Hidden form field that humans never see or fill. Submissions carrying a
# value are bots; they get an unspecific error so nothing is learnable.
HONEYPOT_FIELD = "website"


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


class GoogleAuthView(APIView):
    """Sign in (or up) with a Google ID token.

    Google accounts are hard to mass-create, which is the platform's main
    defence against throwaway signups — there is no open password signup.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        try:
            claims = verify_id_token(request.data.get("credential"))
        except GoogleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        email = claims["email"].lower()
        user = User.objects.filter(email=email).first()
        created = user is None
        if created:
            user = User(
                email=email,
                first_name=claims.get("given_name", ""),
                last_name=claims.get("family_name", ""),
                is_email_verified=True,
            )
            user.set_unusable_password()
            user.save()
        elif not user.is_active:
            return Response(
                {"detail": "This account is disabled."}, status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    """Email/password signup, defended against throwaway and bot accounts:
    disposable-domain blocklist, alias-collapsed email uniqueness, honeypot,
    strict per-IP rate limit, and Django's password validators."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        if request.data.get(HONEYPOT_FIELD):
            return Response(
                {"detail": "Registration failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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
    """Password login for pre-existing/admin accounts; no open signup exists."""

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


class MeView(generics.RetrieveUpdateAPIView):
    """Profile of the authenticated user; PATCH updates phone, location, school."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
