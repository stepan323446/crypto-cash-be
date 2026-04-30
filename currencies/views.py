from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.generics import ListAPIView

from .models import FiatCurrency
from .serializer import FiatCurrencySerializer


@method_decorator(cache_page(60 * 15), name='dispatch')
class FiatCurrencyListView(ListAPIView):
    queryset = FiatCurrency.objects.all()
    serializer_class = FiatCurrencySerializer
    pagination_class = None    