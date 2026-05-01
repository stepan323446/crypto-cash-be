from rest_framework import serializers
from .models import FiatCurrency, CryptoCoin, CryptoNetwork, BlockchainAsset, CryptoCategory

class FiatCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FiatCurrency
        fields = ('id', 'name', 'code', 'symbol', 'conversion_rate', 'display_name', 'display_sign_name')

class CryptoNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoNetwork
        fields = ('id', 'name', 'icon', 'type', 'native_asset', 'explorer_url')

class CryptoNetworkShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoNetwork
        fields = ('id', 'name', 'icon')

class CryptoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCategory
        fields = ('id', 'name',)

class CryptoCoinShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCoin
        fields = ('id', 'name', 'code', 'slug', 'icon', 'price', 'change_24h', 'market_cap', 'trading_vol_24h')

class BlockchainAssetSerializer(serializers.ModelSerializer):
    network_detail = CryptoNetworkShortSerializer(source='network')

    class Meta:
        model = BlockchainAsset
        fields = (
            'id', 'type', 'address',
            'network', 'network_detail', 'precision',
            'coin'
        )

class CryptoCoinSerializer(serializers.ModelSerializer):
    parent_coin_detail = CryptoCoinShortSerializer(source='parent_coin', read_only=True)
    categories_detail = CryptoCategorySerializer(source='categories', many=True, read_only=True)
    primary_chain = CryptoNetworkShortSerializer(source='origin_asset.network', read_only=True)

    class Meta:
        model = CryptoCoin
        fields = (
            'id', 
            'name', 
            'code',
            'slug',
            'icon',
            'coingecko_id',
            'website_urls', 
            'parent_coin', 'parent_coin_detail',
            'primary_chain', 
            'description', 'issue_date', 'static_extra_data', 
            'price', 'change_24h', 'market_cap', 'trading_vol_24h',
            'extra_data', 
            'categories', 'categories_detail',
            'time_created', 'time_updated'
        )