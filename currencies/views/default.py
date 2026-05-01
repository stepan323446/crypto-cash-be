from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema

from currencies.filters import CryptoCoinFilter
from currencies.models import FiatCurrency, CryptoCoin, CryptoCategory, BlockchainAsset
from currencies.serializers import (
    FiatCurrencySerializer, CryptoCoinShortSerializer,
    CryptoCategorySerializer, CryptoCoinSerializer,
    BlockchainAssetSerializer
)


@extend_schema(
    tags=["Currency"],
    summary="List all fiat currencies",
    description="Returns a complete list of supported fiat currencies (USD, EUR, etc.) without pagination."
)
@method_decorator(cache_page(60 * 15), name='dispatch')
class FiatCurrencyListView(ListAPIView):
    queryset = FiatCurrency.objects.all()
    serializer_class = FiatCurrencySerializer
    pagination_class = None    

@extend_schema(
    tags=["Crypto"],
    summary="List crypto categories",
    description="Retrieve a list of all cryptocurrency categories (e.g., DeFi, NFT, Layer 1)."
)
class CryptoCategoryListView(ListAPIView):
    queryset = CryptoCategory.objects.all()
    serializer_class = CryptoCategorySerializer
    pagination_class = None

@extend_schema(
    tags=["Crypto"],
    summary="List crypto coins with filtering",
    description="Get a list of crypto coins with support for searching by name/code and ordering by market cap, price, or volume."
)
class CryptoCoinListView(ListAPIView):
    queryset = CryptoCoin.objects.all().distinct()
    serializer_class = CryptoCoinShortSerializer

    filterset_class = CryptoCoinFilter
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    ordering_fields = ['price', 'market_cap', 'change_24h', 'trading_vol_24h']
    ordering = ['-market_cap']
    search_fields = ['name', 'code']

@extend_schema(
    tags=["Crypto"],
    summary="Get coin details by code",
    description="Retrieve detailed information about a specific cryptocurrency using its ticker code (e.g., 'BTC')."
)
class CryptoCoinRetrieveView(RetrieveAPIView):
    queryset = CryptoCoin.objects.with_full_relations()
    serializer_class = CryptoCoinSerializer
    lookup_field = 'slug'

@extend_schema(
    tags=["Crypto"],
    summary="Get coin details by ID",
    description="Retrieve detailed information about a specific cryptocurrency using its primary key (integer ID)."
)
class CryptoCoinRetrieveByIdView(CryptoCoinRetrieveView):
    lookup_field = 'pk'

@extend_schema(
    tags=["Crypto"],
    summary="List blockchain assets",
    description=(
        "Retrieve a list of blockchain assets with their associated networks. "
        "Supports searching by contract address or network name, and filtering by coin or network ID."
    )
)
class BlockchainAssetListView(ListAPIView):
    queryset = BlockchainAsset.objects.with_network()
    serializer_class = BlockchainAssetSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    ordering = ['-id']
    search_fields = ['address', 'network__name']
    filterset_fields = ['coin', 'network']