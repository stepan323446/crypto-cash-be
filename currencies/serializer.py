from rest_framework import serializers
from .models import FiatCurrency

class FiatCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FiatCurrency
        fields = ('id', 'name', 'code', 'symbol', 'conversion_rate', 'display_name', 'display_sign_name')

