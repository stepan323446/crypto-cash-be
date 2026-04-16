from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from .utils.otp import verify_totp
from .utils.twofa import TwoFAToken
from .models import User, Currency, UserActionToken, UserActionCode
from .exceptions import AccountNotActivated, AccountToptNoExists
from .validators import AdultValidator, ActionTokenValidator
from .mixins import TwoFAValidationMixin

LOGIN_STATUS_CHOICES = (
    ('finished', 'Finished'),
    ('totp', 'TOTP'),
)

class LoginSerializer(serializers.Serializer):
    login_email         = serializers.CharField(write_only=True)
    password            = serializers.CharField(write_only=True)

    available_challenges = serializers.ChoiceField(choices=['totp', 'email'], read_only=True)
    twofa_token         = serializers.CharField(read_only=True, allow_null=True)

    def validate(self, attrs: dict):
        login_email: str = attrs.get('login_email')
        password: str = attrs.get('password')

        user = User.objects.filter(
            Q(email=login_email) | Q(username=login_email)
        ).first()

        if not user:
            raise serializers.ValidationError({"error": "User not found"}, code=404)
        
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"error": "Invalid credentials"})
        
        if not user.is_active:
            raise AccountNotActivated(user, {"error": "User account is not activated."})
        
        intermediate_token = TwoFAToken.for_user(user)

        available_challenges = ['email']
        if user.totp_enabled:
            available_challenges.append('totp')

        return {
            "available_challenges": available_challenges,
            "twofa_token": str(intermediate_token)
        }
    
class LoginWithTOTPSerializer(TwoFAValidationMixin, serializers.Serializer):
    code                = serializers.CharField(write_only=True, min_length=6, max_length=6)
    twofa_token         = serializers.CharField(write_only=True)

    access_token        = serializers.CharField(read_only=True, allow_null=True)
    refresh_token       = serializers.CharField(read_only=True, allow_null=True)

    def validate(self, attrs: dict):
        code = attrs.get('code')
        twofa_token = attrs.get('twofa_token')

        user = self.get_user_from_token(twofa_token)

        if user.totp_enabled == False:
            raise AccountToptNoExists(user)
        
        if not verify_totp(user.totp_secret, code):
            raise serializers.ValidationError({"code": "Invalid 2FA code."})
        
        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

class SendEmailCodeSerializer(TwoFAValidationMixin, serializers.Serializer):
    twofa_token         = serializers.CharField(write_only=True)

    def validate(self, attrs: dict):
        twofa_token = attrs.get('twofa_token')

        user = self.get_user_from_token(twofa_token)
        self.validated_user = user

        return attrs
    
class LoginWithEmailSerializer(TwoFAValidationMixin, serializers.Serializer):
    code                = serializers.CharField(write_only=True, max_length=10)
    twofa_token         = serializers.CharField(write_only=True)

    access_token        = serializers.CharField(read_only=True, allow_null=True)
    refresh_token       = serializers.CharField(read_only=True, allow_null=True)

    def validate(self, attrs: dict):
        twofa_token = attrs.get('twofa_token')
        code = attrs.get('code')

        user = self.get_user_from_token(twofa_token)
        user_action_code = UserActionCode.get_action_by_user(user, UserActionCode.ActionTypes.AUTHORIZATION, code)

        if not user_action_code:
            raise serializers.ValidationError({"code": "Invalid authorization code" })

        user_action_code.is_used = True
        user_action_code.save()
        
        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        }
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        self.user = user
        
        return attrs
    
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128, required=True, validators=[ActionTokenValidator(UserActionToken.ActionTypes.PASSWORD_RESET)])
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    date_of_birth = serializers.DateField(
        required=True,
        validators=[AdultValidator()]
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'date_of_birth', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_active=False)
        return user
    
class ActivateUserSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128, required=True, validators=[ActionTokenValidator(UserActionToken.ActionTypes.ACTIVATION)])

class TOTPUserSecretSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('totp_secret',)

class TOTPActivationSerializer(serializers.ModelSerializer):
    code = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = ('code', 'totp_enabled')
        extra_kwargs = {
            'totp_enabled': {'read_only': True}
        }

    def validate(self, attrs: dict):
        code = attrs.get('code')
        user: User = self.instance

        if not user.totp_secret:
            raise serializers.ValidationError(
                {"error": "TOTP secret not found. Generate it first."})
        
        if not verify_totp(user.totp_secret, code):
            raise serializers.ValidationError(
                {"code": "Invalid or expired activation code."})
        
        return attrs
    
    def update(self, instance: User, validated_data):
        instance.totp_enabled = True
        instance.save()
        return instance

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('id', 'code', 'name', 'symbol', 'conversion_rate')

class UserSerializer(serializers.ModelSerializer):
    email               = serializers.EmailField(read_only=True)
    currency_detail     = CurrencySerializer(source="currency", read_only=True)

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'date_of_birth',
            'email',
            'lang',
            'totp_enabled',
            'currency',
            'currency_detail'
        )
        extra_kwargs = {
            'totp_enabled': {'read_only': True}
        }
