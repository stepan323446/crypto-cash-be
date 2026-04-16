from rest_framework_simplejwt.tokens import Token
from datetime import timedelta

class TwoFAToken(Token):
    token_type = 'twofa_intermediate'
    lifetime = timedelta(minutes=10)

    def get_user_id(self):
        return self.payload.get('user_id')