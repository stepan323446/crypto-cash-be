import secrets
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied
from django.db import models

from datetime import timedelta
from project.utils.cryptography import generate_random_code

# Create your models here.
class User(AbstractUser):
    email                = models.EmailField(unique=True)
    first_name           = models.CharField(max_length=150, blank=False)
    last_name            = models.CharField(max_length=150, blank=False)
    date_of_birth        = models.DateField(null=True, blank=True)
    lang                 = models.CharField(max_length=10, default="en")
    totp_secret          = models.CharField(max_length=255, blank=True, null=True)
    totp_enabled         = models.BooleanField(default=False)
    currency: "Currency" = models.ForeignKey("Currency", on_delete=models.SET_DEFAULT, default=1)

    def __str__(self):
        return self.username
    
class Currency(models.Model):
    code             = models.CharField(max_length=20, unique=True)
    name             = models.CharField(max_length=30, blank=True, null=True)
    symbol           = models.CharField(max_length=5, blank=True, null=True)
    conversion_rate  = models.FloatField(default=1, verbose_name='Coversion rate (USD to ...)')

    time_created     = models.DateTimeField(auto_now_add=True)
    time_updated     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return super().__str__()
    
    def delete(self, *args, **kwargs):
        if self.code == 'USD':
            raise PermissionDenied("You cannot delete default model USD")
        
        return super().delete(*args, **kwargs)
    
class UserActionSecret(models.Model):
    EXPIRED_THRESHOLD = timedelta(minutes=5)

    user: "User"        = models.ForeignKey('User', on_delete=models.CASCADE)
    action_type         = models.CharField(max_length=20)

    created_at          = models.DateTimeField(auto_now_add=True)
    is_used             = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @classmethod
    def get_action_by_user(cls, user: User, action: str):
        expired_threshold = timezone.now() - cls.EXPIRED_THRESHOLD
        return cls.objects.filter(
            user=user, 
            action_type=action, 
            created_at__gt=expired_threshold,
            is_used=False
        ).first()
    
    @property
    def is_expired(self):
        expired_threshold = timezone.now() - self.EXPIRED_THRESHOLD
        return self.created_at < expired_threshold
    
    @property
    def is_active(self):
        return not (self.is_expired or self.is_used)

class UserActionToken(UserActionSecret):
    class ActionTypes(models.TextChoices):
        ACTIVATION = 'activation', 'Activation'
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    token               = models.CharField(max_length=128, unique=True)
    action_type         = models.CharField(max_length=20, choices=ActionTypes.choices)
    value               = models.CharField(max_length=150, null=True, blank=True)

    @classmethod
    def create_action_token(cls, user: User, action: ActionTypes):
        token = secrets.token_hex(32)
        return cls.objects.create(user=user, action_type=action, token=token)

    def __str__(self):
        return f'Token {self.action_type} at {self.created_at}'
    
class UserActionCode(UserActionSecret):
    class ActionTypes(models.TextChoices):
        AUTHORIZATION = 'authorization', 'Authorization'

    code                = models.CharField(max_length=10)
    action_type         = models.CharField(max_length=20, choices=ActionTypes.choices)
    
    @classmethod
    def get_action_by_user(cls, user: User, action: str, code: str = None):
        expired_threshold = timezone.now() - cls.EXPIRED_THRESHOLD
        queryset = cls.objects.filter(
            user=user, 
            action_type=action, 
            created_at__gt=expired_threshold,
            is_used=False
        )
        if code:
            queryset = queryset.filter(code=code)

        return queryset.first()

    @classmethod
    def create_action_code(cls, user: User, action: ActionTypes, length=6):
        code = generate_random_code(length)
        return cls.objects.create(user=user, action_type=action, code=code)

    def __str__(self):
        return f'Code {self.action_type} at {self.created_at}'

    