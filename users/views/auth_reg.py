from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from drf_spectacular.utils import extend_schema

from project.utils.serializers import DetailSerializer

from users.models import User, UserActionToken
from users.serializers import (
    RegisterSerializer, 
    ActivateUserSerializer
)
from users.tasks import activation_email

@extend_schema(tags=["Auth"], 
               summary="Sign up new user in the system CryptoCash",
               request=RegisterSerializer,
               responses=DetailSerializer)
class RegisterUserView(APIView):
    def post(self, request: Request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()

        action_token = UserActionToken.create_action_token(
            user, 
            UserActionToken.ActionTypes.ACTIVATION
        )
        activation_email.delay(
            user_username=user.username,
            user_email=user.email,
            activation_token=action_token.token
        )
        return Response({
            "detail": "User registered successfully. Please check your email for activation."
        }, status=status.HTTP_201_CREATED)
    
@extend_schema(tags=["Auth"], 
               summary="Activate user account using email token",
               request=ActivateUserSerializer,
               responses=DetailSerializer)
class ActivateUserView(APIView):
    def post(self, request: Request):
        serializer = ActivateUserSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        with transaction.atomic():
            user_action = UserActionToken.objects.select_for_update().select_related('user').get(token=token)
            
            user_action.is_used = True
            user_action.save()

            user = user_action.user
            user.is_active = True
            user.generate_memo()
            user.save()

        return Response({
            "detail": "User activated successfully."
        })