from django.core.exceptions import ValidationError

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework import permissions as rest_perms
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from project.utils.serializers import DetailSerializer

from users.models import User
from users.utils.otp import generate_secret_totp
from users.serializers import (
    UserSerializer,
    TOTPUserSecretSerializer,
    TOTPActivationSerializer
)

@extend_schema(tags=["User"], 
               summary="Retrieve or update the current user's profile.",
               responses=UserSerializer)
class UserInfoView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (rest_perms.IsAuthenticated,)

    def get_object(self):
        return self.request.user
    
@extend_schema(tags=["User"], 
               summary="Create TOTP secret but without activation",
               responses=TOTPUserSecretSerializer)
class CreateTOTPSecretView(APIView):
    permission_classes = [rest_perms.IsAuthenticated]
    def post(self, request: Request):
        user: User = request.user
        
        if user.totp_enabled:
            raise ValidationError({"detail": "You already activated 2FA TOTP"})

        user.totp_secret = generate_secret_totp()
        user.save()
        
        serializer = TOTPUserSecretSerializer(user)

        return Response(serializer.data)

@extend_schema(tags=["User"], 
               summary="Create TOTP secret but without activation",
               request=TOTPActivationSerializer,
               responses=DetailSerializer)
class ActivateTOTPView(APIView):
    permission_classes = [rest_perms.IsAuthenticated]

    def post(self, request: Request):
        user: User = request.user
        serializer = TOTPActivationSerializer(instance=user, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({"detail": "2FA activated"})
    
@extend_schema(tags=["User"], 
               summary="Disable TOTP 2FA Authorization",
               responses=DetailSerializer)
class DisableTOTPView(APIView):
    permission_classes = [rest_perms.IsAuthenticated]

    def post(self, request: Request):
        user: User = request.user
        
        user.totp_enabled = False
        user.totp_secret = None
        user.save()
        
        return Response({"detail": "2FA deactivated"})