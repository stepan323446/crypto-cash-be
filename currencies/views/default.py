from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404

from rest_framework import filters
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from currencies.utils.api import get_coingecko_marketchart
from currencies.filters import CryptoCoinFilter
from currencies.models import FiatCurrency, CryptoCoin, CryptoCategory, BlockchainAsset
from currencies.serializers import (
    FiatCurrencySerializer, CryptoCoinShortSerializer,
    CryptoCategorySerializer, CryptoCoinSerializer,
    BlockchainAssetSerializer, CryptoCoinChartSerializer
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

class CryptoCoinChartView(APIView):
    @extend_schema(
        tags=["Crypto"],
        summary="Get coin market chart data",
        description=(
            "Retrieves historical price, market cap, and volume data for a specific coin. "
            "Returns a list of points where each point is [timestamp, value]."
        ),
        parameters=[
            OpenApiParameter(
                name='slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="The symbol of the cryptocurrency (e.g., 'btc', 'eth')",
                required=True,
            ),
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Data period",
                enum=['1d', '30d', '90d', '365d', 'max'],
                default='1d',
            ),
        ],
        responses={200: CryptoCoinChartSerializer}
    )
    def get(self, request: Request):
        # Get params from GET query
        slug = request.query_params.get('slug')
        days_param = request.query_params.get('days', '1d')

        # Mapping to coingecko format
        days_map = {
            '1d': 1,
            '30d': 30,
            '90d': 90,
            '365d': 365,
            'max': 'max'
        }

        if days_param not in days_map:
            return Response({"error": "Invalid days format"}, status=400)

        # Cache
        cache_key = f'chart_{slug}_{days_param}'
        cache_time = 3600 if days_param == '1d' else 21600

        data = cache.get(cache_key)

        if not data:
            crypto_coin = get_object_or_404(CryptoCoin, slug=slug)
            gecko_days = days_map[days_param]
            
            try:
                gecko_chart = get_coingecko_marketchart(
                    coin_id=crypto_coin.coingecko_id,
                    days=gecko_days
                )
                data = gecko_chart.model_dump()
                cache.set(cache_key, data, timeout=cache_time)
            except Exception as e:
                return Response({"error": str(e)}, status=502)

        serializer = CryptoCoinChartSerializer(data)
        return Response(serializer.data)