import jwt, datetime, requests
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

from .local_settings import *

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from .serializers import UserSerializer
from .local_settings import *
from pathlib import Path

# Load PRIVATE_KEY buat sign internal token
PRIVATE_KEY = Path(BASE_DIR, "keys/private.pem").read_text()

User = get_user_model()

@extend_schema(tags=['Auth'])
class AuthViewSet(viewsets.ViewSet):

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
            try:
                resp = requests.get(
                    f"{HR_SERVICE}/api/hr/master/employee/?user_id={user.pk}&exclude=parent,children",
                    headers={"Authorization": f"Bearer {internal_token}"},
                    timeout=5
                )

                if resp.status_code == 200:
                    results = resp.json().get('results', [])
                    employee_data = results[0] if results else None
                
                else:
                    employee_data = {"detail": f"HR service error {resp.status_code}"}
            
            except requests.RequestException as e:
                employee_data = {"detail": f"HR service unreachable: {str(e)}"}

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