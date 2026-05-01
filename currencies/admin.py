from django.contrib import admin
from .models import FiatCurrency, CryptoNetwork, CryptoCoin, BlockchainAsset, CryptoCategory

# Register your models here.
@admin.register(FiatCurrency)
class FiatCurrencyAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'code', 'time_created', 'time_updated')
    search_fields = ('code', 'name', 'symbol')
    readonly_fields = ('time_created', 'time_updated')

@admin.register(CryptoNetwork)
class CryptoNetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')

@admin.register(CryptoCoin)
class CryptoCoinAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'slug', 'price', 'change_24h', 'time_updated')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'code')
    readonly_fields = ('price', 'change_24h', 'market_cap', 'trading_vol_24h', 'extra_data', 'time_created', 'time_updated')

@admin.register(BlockchainAsset)
class BlockchainAssetAdmin(admin.ModelAdmin):
    list_display = ('coin', 'network', 'type')
    list_filter = ('type', 'network')
    search_fields = ('coin__name', 'address')

@admin.register(CryptoCategory)
class CryptoCategoryAdmin(admin.ModelAdmin):
    pass