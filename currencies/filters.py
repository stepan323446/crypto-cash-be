from django_filters import rest_framework as filters
from .models import CryptoCoin

class CryptoCoinFilter(filters.FilterSet):
    network = filters.NumberFilter(field_name="origin_asset__network__id")
    categories = filters.AllValuesMultipleFilter(field_name="categories__id")

    class Meta:
        model = CryptoCoin
        fields = ['network', 'categories']