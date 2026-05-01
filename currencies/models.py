from decimal import Decimal
from django.db import models
from .schemas import (
    StaticExtraDataSchema,
    DynamicExtraDataSchema
)
from .managers import CryptoCoinManager, BlockchainAssetManager

# Create your models here.
class FiatCurrency(models.Model):
    code             = models.CharField(max_length=20, unique=True)
    name             = models.CharField(max_length=30, blank=True, null=True)
    symbol           = models.CharField(max_length=5, blank=True, null=True)
    conversion_rate  = models.DecimalField(default=1.0, max_digits=18, decimal_places=8, verbose_name='Coversion rate (USD to ...)')

    time_created     = models.DateTimeField(auto_now_add=True)
    time_updated     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fiat Currency"
        verbose_name_plural = "Fiat Currencies"

    @property
    def display_name(self):
        return self.name if self.name else self.code
    
    @property
    def display_sign_name(self):
        return self.symbol if self.symbol else self.code

    def __str__(self):
        return f"{self.code} ({self.symbol})"
    
class CryptoCategory(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

class CryptoNetwork(models.Model):
    class NetworkTypes(models.TextChoices):
        TON = 'ton', 'TON'
    name            = models.CharField(max_length=20)
    type            = models.CharField(max_length=15, choices=NetworkTypes.choices, unique=True)
    icon            = models.ImageField('currencies/network/', null=True, blank=True)
    native_asset: "BlockchainAsset" = models.OneToOneField("BlockchainAsset", null=True, blank=True, on_delete=models.SET_NULL, related_name="network_primary_for")
    explorer_url    = models.CharField(max_length=255, null=True, blank=True, help_text="Exporer url with format {address}")

    def __str__(self):
        return self.name
    
    def get_address_url(self, address: str):
        return self.explorer_url.format(address=address)

class CryptoCoin(models.Model):
    # static
    name            = models.CharField(max_length=50)
    code            = models.CharField(max_length=15, unique=True, db_index=True)
    slug            = models.SlugField(max_length=50, unique=True, db_index=True)
    icon            = models.ImageField(null=True, blank=True, upload_to='currencies/coins/')
    coingecko_id    = models.CharField(max_length=40)
    website_urls    = models.TextField(null=True, blank=True, help_text="Website urls (divided by ;)")
    parent_coin: "CryptoCoin" = models.ForeignKey("self", blank=True, null=True, on_delete=models.PROTECT, verbose_name="Parent coin (if wrapped)")
    origin_asset: "BlockchainAsset" = models.ForeignKey(
        "BlockchainAsset", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="is_origin_for"
    )
    description     = models.TextField()
    issue_date      = models.DateField()
    static_extra_data = models.JSONField(default=dict, blank=True)

    # Dynamic
    price           = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    change_24h      = models.FloatField(default=0)
    market_cap      = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    trading_vol_24h = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    extra_data      = models.JSONField(default=dict, blank=True)

    time_created     = models.DateTimeField(auto_now_add=True)
    time_updated     = models.DateTimeField(auto_now=True)

    categories      = models.ManyToManyField(CryptoCategory, related_name='categories')

    objects: CryptoCoinManager["CryptoCoin"] = CryptoCoinManager()

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def static_metadata(self):
        return StaticExtraDataSchema(**self.static_extra_data)
    
    def set_static_metadata(self, data: StaticExtraDataSchema):
        self.static_extra_data = data.model_dump(mode='json')

    @property 
    def dynamic_metadata(self):
        return DynamicExtraDataSchema(**self.extra_data)
    
    def set_dynamic_metadata(self, data: DynamicExtraDataSchema):
        self.extra_data = data.model_dump(mode='json')

class BlockchainAsset(models.Model):
    class AssetType(models.TextChoices):
        NATIVE = 'native', 'Native'
        CONTRACT = 'contract', 'Contract'

    network         = models.ForeignKey(CryptoNetwork, null=True, on_delete=models.SET_NULL)
    type            = models.CharField(max_length=20, choices=AssetType.choices, default=AssetType.CONTRACT)
    address         = models.CharField(max_length=255, null=True, blank=True, help_text="Contract address (empty for native)")
    precision       = models.IntegerField()
    coin            = models.ForeignKey(CryptoCoin, null=True, on_delete=models.SET_NULL)

    objects: BlockchainAssetManager['BlockchainAsset'] = BlockchainAssetManager()

    class Meta:
        unique_together = ('coin', 'network')

    def __str__(self):
        return f"{self.coin.code} on {self.network.name}"
    
    def get_atomic_amount(self, amount: Decimal | float | str) -> int:
        d_amount = Decimal(str(amount)) 
        return int(d_amount * (Decimal(10) ** self.precision))

    def from_atomic_amount(self, atomic_amount: int) -> Decimal:
        return Decimal(atomic_amount) / (Decimal(10) ** self.precision)