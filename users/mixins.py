from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .utils.twofa import TwoFAToken
from .models import User


class TwoFAValidationMixin:
    def get_user_from_token(self, twofa_token):
        try:
            token_obj = TwoFAToken(twofa_token)
            user_id = token_obj.get_user_id()  # или .payload.get('user_id')
            return User.objects.get(id=user_id)
            
        except (TokenError, InvalidToken):
            raise serializers.ValidationError(
                {"twofa_token": "Auth Session is invalid or expired."}, 
                code="invalid_token"
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"error": "User not found."}, 
                code="user_not_found"
            )