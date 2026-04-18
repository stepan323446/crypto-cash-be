from django.db import transaction
from django.core.exceptions import ValidationError

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework import permissions as rest_perms
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from project.utils.serializers import DetailSerializer

from users.models import User, UserActionToken
from users.tasks import change_new_email
from users.utils.otp import generate_secret_totp
from users.serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    TOTPUserSecretSerializer,
    TOTPActivationSerializer,
    ChangeEmailSerializer,
    ChangeEmailCompleteSerializer
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
               summary="Update current user's password",
               request=ChangePasswordSerializer,
               responses=UserSerializer)
class ChangePasswordView(APIView):
    permission_classes = [rest_perms.IsAuthenticated]
    def post(self, request: Request):
        user: User = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(old_password):
            return Response(
                {"old_password": ["Old password is not correct"]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password changed successfully"}, 
            status=status.HTTP_200_OK
        )

@extend_schema(tags=["User"], 
               summary="Send request to change email",
               request=ChangeEmailSerializer,
               responses=DetailSerializer)
class ChangeEmailView(APIView):
    permission_classes = [rest_perms.IsAuthenticated]
    def post(self, request: Request):
        user: User = request.user
        serializer = ChangeEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        new_email = serializer.validated_data['new_email']

        if not user.check_password(password):
            return Response(
                {"old_password": ["Password is not correct"]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = UserActionToken.get_action_by_user(user, UserActionToken.ActionTypes.EMAIL_CHANGE)
        if token:
            token.delete()

        token = UserActionToken.create_action_token(user, UserActionToken.ActionTypes.EMAIL_CHANGE, new_email)
        change_new_email.delay(
            user_username=user.username,
            new_user_email=token.value,
            confirmation_token=token.token
        )

        return Response(
            {"message": "A confirmation email has been sent to your new email address."},
            status=status.HTTP_200_OK
        )

@extend_schema(tags=["User"], 
               summary="Complete changing email with token",
               request=ChangeEmailCompleteSerializer,
               responses=DetailSerializer)
class ChangeEmailCompleteView(APIView):
    def post(self, request: Request):
        serializer = ChangeEmailCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data['token']
        token = UserActionToken.objects.select_related('user').get(token=token_str)
        user = token.user

        with transaction.atomic():
            token.is_used = True
            user.email = token.value

            token.save()
            user.save()

        return Response(
            {"message": "E-mail was successfully changed"},
        )

    
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