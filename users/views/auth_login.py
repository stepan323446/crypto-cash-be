from django.db import transaction
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.utils import extend_schema

from project.utils.serializers import DetailSerializer
from users.models import UserActionToken
from users.serializers import (
    LoginSerializer,
    LoginWithTOTPSerializer,
    SendEmailCodeSerializer,
    LoginWithEmailSerializer,
    ForgotPasswordSerializer, 
    ResetPasswordSerializer
)
from users.models import User, UserActionCode
from users.exceptions import AccountNotActivated
from users.tasks import activation_email, authorization_email, forgot_pass_email, reset_pass_email_completed

@extend_schema(tags=["Auth"])
class MyTokenObtainPairView(TokenObtainPairView):
    pass

@extend_schema(tags=["Auth"])
class MyTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(tags=["Auth"])
class MyTokenVerifyView(TokenVerifyView):
    pass

@extend_schema(tags=["Auth"], 
               summary="Auth user in his account with username/email and password",
               request=LoginSerializer,
               responses=LoginSerializer)
class LoginView(APIView):
    def post(self, request: Request):
        serializer = LoginSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            
        except AccountNotActivated as ex:
            user = ex.user

            action_token = UserActionToken.get_action_by_user(
                user, 
                UserActionToken.ActionTypes.ACTIVATION
            )

            if not action_token:
                action_token = UserActionToken.create_action_token(user, UserActionToken.ActionTypes.ACTIVATION)

                activation_email.delay(user_username=user.username, 
                                        user_email=user.email, 
                                        activation_token=action_token.token)

            return Response({
                "detail": "Account is not activated. Activation email sent.",
            }, status=status.HTTP_403_FORBIDDEN)

        return Response(serializer.validated_data)

@extend_schema(tags=["Auth"], 
               summary="Auth with 2FA TOPT",
               request=LoginWithTOTPSerializer,
               responses=LoginWithTOTPSerializer)
class LoginWithTOTPView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_throttle'

    def post(self, request: Request):
        serializer = LoginWithTOTPSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

@extend_schema(tags=["Auth"], 
               summary="Sends a verification code to the user's email. Requires a valid `twofa_token` from the login step.",
               request=SendEmailCodeSerializer,
               responses=DetailSerializer)
class SendTwoFACodeView(APIView):
    def post(self, request: Request):
        serializer = SendEmailCodeSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user: User = serializer.validated_user

        action_code = UserActionCode.get_action_by_user(user, UserActionCode.ActionTypes.AUTHORIZATION)

        if action_code:
            return Response({"detail": "A verification code has already been sent to your email. Please check your inbox."}, status=status.HTTP_400_BAD_REQUEST)

        action_code = UserActionCode.create_action_code(user, UserActionCode.ActionTypes.AUTHORIZATION)

        authorization_email.delay(
            user_username=user.username, 
            user_email=user.email,
            code=action_code.code    
        )
        return Response({"detail": "Code sent successfully."})

@extend_schema(tags=["Auth"], 
               summary="Auth with 2FA E-mail",
               request=LoginWithEmailSerializer,
               responses=LoginWithEmailSerializer)
class LoginWithEmailView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_throttle'

    def post(self, request: Request):
        serializer = LoginWithEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

@extend_schema(
    tags=["Auth"],
    summary="Request password reset",
    description=(
        "Initiates the password recovery process. "
        "Checks if the user exists by email and sends a reset link containing a unique token. "
        "A reset link can only be requested once every 3 hours (or until the current one expires)."
    ),
    request=ForgotPasswordSerializer,
    responses=DetailSerializer
)
class ForgotPasswordView(APIView):
    def post(self, request: Request):
        serializer = ForgotPasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.user

        action_token = UserActionToken.get_action_by_user(
            user, 
            UserActionToken.ActionTypes.PASSWORD_RESET
        )

        if action_token:
            return Response(
                {"detail": "A reset link has already been sent. Please check your email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        action_token = UserActionToken.create_action_token(user, UserActionToken.ActionTypes.PASSWORD_RESET)
        forgot_pass_email.delay(user_username=user.username, 
                                user_email=user.email, 
                                reset_token=action_token.token)
            
        return Response({"detail": "Reset link successfully sent."})
    
@extend_schema(
    tags=["Auth"],
    summary="Reset password using token",
    description=(
        "Completes the password reset process. "
        "Requires a valid, unused token from the reset email and a new password. "
        "After a successful reset, the token is invalidated, and a confirmation email is sent to the user."
    ),
    request=ResetPasswordSerializer,
    responses=DetailSerializer
)
class ResetPasswordView(APIView):
    def post(self, request: Request):
        serializer = ResetPasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        with transaction.atomic():
            user_action = UserActionToken.objects.select_for_update().select_related('user').get(token=token)
            user_action.is_used = True
            user_action.save()

            user = user_action.user
            user.set_password(new_password)
            user.save()

        reset_pass_email_completed.delay(
            user_username=user.username, 
            user_email=user.email
        )
            
        return Response({
            "detail": "Password changed successfully."
        })