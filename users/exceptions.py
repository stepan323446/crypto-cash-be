from rest_framework.exceptions import APIException
from .models import User

class AccountNotActivated(APIException):
    status_code = 403
    default_detail = "User account is not activated."
    default_code = 'account_not_activated'
    
    def __init__(self, user: User, *args, **kwargs):
        self.user = user

        super().__init__(*args, **kwargs)

class AccountToptNoExists(APIException):
    status_code = 403
    default_detail = "User account hasn't topt method authorization."

    def __init__(self, user: User, *args, **kwargs):
        self.user = user

        super().__init__(*args, **kwargs)