import jwt, datetime, requests, subprocess
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.http import HttpResponse

from .local_settings import *
from .filters import *
from .serializers import GitSerializer, UserSerializer
from .local_settings import *
from .config import fetch_external_data

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.types import OpenApiTypes

from pathlib import Path

from django.conf import settings
    
from prometheus_client import generate_latest, REGISTRY

# Load PRIVATE_KEY buat sign internal token
PRIVATE_KEY = Path(settings.BASE_DIR, "keys/private.pem").read_text()

User = get_user_model()

@extend_schema(tags=['Auth'])
class AuthViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer

    # ================= LOGIN =================
    @method_decorator(csrf_exempt)
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'},
                },
                'required': ['username', 'password']
            }
        },
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login_view(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        session_id = request.session.session_key

        # Buat internal token (valid 10 menit misalnya)
        payload = {
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            "iat": datetime.datetime.utcnow(),
            "iss": "AUTH_SERVICE"
        }
        internal_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

        employee_data = None
        if not user.is_superuser:
            employee_data = fetch_external_data(
                service_name="HR",
                endpoint=f"{HR_SERVICE}/api/hr/master/employee/?user_id={user.pk}&exclude=parent,children,created_at,updated_at,created_by,updated_by,deleted_at,deleted_by",
                key_suffix=f"employee:{user.pk}",
                timeout=600,
                retries=2,
                fallback=True
            )
            if employee_data and "results" in employee_data:
                results = employee_data.get("results", [])
                employee_data = results[0] if results else None
            elif employee_data is None:
                employee_data = {"detail": "HR service unreachable or failed after retries"}
            else:
                employee_data = {"detail": "HR service returned unexpected data"}

        resp =  Response({
            'sessionid': session_id,
            'internal_token': internal_token,
            'user_data': UserSerializer(user, context={'request': request}).data,
            'employee_data': employee_data
        }, status=status.HTTP_200_OK)

        resp.set_cookie(
            key="sessionid",
            value=session_id,
            httponly=True,
            samesite="Lax"
        )

        return resp

    # ================= LOGOUT =================
    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'], url_path='logout')
    def logout_view(self, request):
        request.session.flush()
        logout(request)
        return Response({'message': 'Logout berhasil'}, status=status.HTTP_200_OK)

    # ================= VERIFY SESSION (frontend) =================
    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['post'], url_path='verify-session')
    def verify_session_view(self, request):
        sessionid = request.COOKIES.get("sessionid")
        if not sessionid:
            return Response({"detail": "Missing sessionid"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            session = Session.objects.get(session_key=sessionid)
            uid = session.get_decoded().get('_auth_user_id')
            user = User.objects.get(pk=uid)

            # Kalau mau sekalian generate internal_token
            payload = {"user_id": user.id}
            internal_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

            return Response({
                "valid": True,
                "user_id": user.id,
                "internal_token": internal_token
            }, status=status.HTTP_200_OK)

        except Session.DoesNotExist:
            return Response({"detail": "Invalid session"}, status=status.HTTP_401_UNAUTHORIZED)

    # ================= CHANGE PASSWORD =================
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        user = request.user
        old = request.data.get('old_password')
        new = request.data.get('new_password')

        if not old or not new:
            return Response({'detail': 'Both old_password and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old):
            return Response({'detail': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new)  # ✅ pakai new, bukan old
        user.save()

        return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["User"])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filterset_class = UserFilter

    @extend_schema(
        description="Ambil daftar user dengan pagination & filter.",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description="Return which page you want to return."),
            OpenApiParameter("page_size", OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description="Return the count of data each page."),
            OpenApiParameter("page_size", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Return the count of data each page."),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Search based on username (WHERE LIKE %<value>%) and email (WHERE LIKE %<value>%)"),
            OpenApiParameter("fields", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Only get the fields you want\n\nexample:\n\n?fields=username,email,is_active"),
            OpenApiParameter("exclude", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Remove the fields you want\n\nexample:\n\n?exclude=first_name,last_name,date_joined,last_login")
        ],
        responses={200: UserSerializer}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

# Endpoint untuk expose metrics ke Prometheus
def metrics_view(request):
    return HttpResponse(generate_latest(REGISTRY), content_type="text/plain; charset=utf-8")

@extend_schema(tags=["Git"])
class GitViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GitSerializer,
        responses={
            200: OpenApiExample(
                "Success",
                value={"status": "success", "output": "Already up to date.\n"}
            ),
            401: OpenApiExample(
                "Invalid credentials",
                value={"status": "error", "error": "Invalid credentials"}
            ),
            403: OpenApiExample(
                "Forbidden",
                value={"status": "forbidden", "error": "Only superusers can pull"}
            ),
        },
    )
    @action(detail=False, methods=['post'])
    def pull(self, request):
        # ambil username & password dari request
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({
                "status": "error",
                "error": "Invalid credentials"
            }, status=401)

        if not user.is_superuser:
            return Response({
                "status": "forbidden",
                "error": "Only superusers can pull"
            }, status=403)

        # kalau lolos validasi → jalankan git pull
        try:
            result = subprocess.run(
                ["git", "pull"],
                capture_output=True,
                text=True,
                cwd="/path/to/your/project"  # sesuaikan
            )

            if result.returncode == 0:
                return Response({
                    "status": "success",
                    "output": result.stdout
                })
            else:
                return Response({
                    "status": "error",
                    "error": result.stderr
                }, status=500)

        except Exception as e:
            return Response({
                "status": "exception",
                "error": str(e)
            }, status=500)