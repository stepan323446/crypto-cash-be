from django.utils import timezone
from rest_framework import serializers

from .models import UserActionToken, UserActionCode

class AdultValidator:
    def __call__(self, value):
        today = timezone.localdate()
        
        age = today.year - value.year - (
            (today.month, today.day) < (value.month, value.day)
        )

        if age < 18:
            raise serializers.ValidationError(
                "You must be at least 18 years old to use CryptoCash.",
                code='too_young'
            )
        
class ActionTokenValidator:
    def __init__(self, action_type: UserActionToken.ActionTypes):
        self.action_type = action_type

    def __call__(self, value):
        try:
            action_token = UserActionToken.objects.get(
                token=value, 
                action_type=self.action_type
            )
        except UserActionToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")

        if not action_token.is_active: 
            raise serializers.ValidationError("Token has already been used or expired.")

        return value