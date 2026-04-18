from django.urls import path, include

from .views import (
    MyTokenObtainPairView,
    MyTokenRefreshView,
    MyTokenVerifyView,
    UserInfoView,
    LoginView,
    CreateTOTPSecretView,
    ActivateTOTPView,
    LoginWithTOTPView,
    DisableTOTPView,
    RegisterUserView,
    ActivateUserView,
    LoginWithEmailView,
    SendTwoFACodeView,
    ResetPasswordView,
    ForgotPasswordView,
    ChangePasswordView,
    ChangeEmailCompleteView,
    ChangeEmailView
)

auth_patterns = [
    path('refresh-token/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginView.as_view(), name="login"),
    path('login-topt/', LoginWithTOTPView.as_view(), name="login-topt"),
    path('register/', RegisterUserView.as_view(), name="register"),
    path('activate/', ActivateUserView.as_view(), name="activate-user"),
    path('send-email-code/', SendTwoFACodeView.as_view(), name="send-email-code-user"),
    path('login-email/', LoginWithEmailView.as_view(), name="login-email-user"),
    path('forgot-password/', ForgotPasswordView.as_view(), name="forgot-password-user"),
    path('reset-password/', ResetPasswordView.as_view(), name="reset-password-user")
]

user_patterns = [
    path('me/', UserInfoView.as_view(), name='user-me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-email-request/', ChangeEmailView.as_view(), name='change-email'),
    path('change-email-complete/', ChangeEmailCompleteView.as_view(), name='change-email-complete'),
    path('create-totp/', CreateTOTPSecretView.as_view(), name='create-totp'),
    path('activate-totp/', ActivateTOTPView.as_view(), name='activate-totp'),
    path('disable-totp/', DisableTOTPView.as_view(), name='disable-totp')
]

urlpatterns = [
    path('v1/', include([
        path('auth/', include(auth_patterns)),
        path('user/', include(user_patterns)),
    ])),
]