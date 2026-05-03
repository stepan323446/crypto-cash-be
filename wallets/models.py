from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from currencies.models import BlockchainAsset
from users.models import User

# Create your models here.
class Wallet(models.Model):
    asset        = models.ForeignKey(BlockchainAsset, on_delete=models.PROTECT)
    balance      = models.DecimalField(max_digits=36, decimal_places=18, default=0)

    holder_type  = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    holder_id    = models.PositiveBigIntegerField(db_index=True)
    holder_object = GenericForeignKey("holder_type", "holder_id")
    
    class Meta:
        unique_together = ('holder_id', 'holder_type', 'asset')

    def __str__(self):
        return f'Holder {self.holder_object} - {self.asset.coin.name} ({self.asset.network})'

class Transaction(models.Model):
    class TransactionTypes(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAW = 'withdraw', 'Withdraw'
        TRANSFER = 'transfer', 'Transfer'
        PAYMENT = 'payment', 'Payment'
        FEE     = 'fee', 'Fee'
        GAS     = 'gas', 'Gas'

    class TransactionDirection(models.TextChoices):
        INTERNAL = 'internal', 'Internal'
        EXTERNAL = 'external', 'External'

    class TransactionStatus(models.TextChoices):
        SUCCESS = 'success', 'Success'
        PENDING = 'pending', 'Pending'
        DENIED = 'denied', 'Denied'

    wallet       = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount       = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    price_at_time = models.DecimalField(max_digits=18, decimal_places=2, help_text="Price at time with USD")
    tx_type      = models.CharField(max_length=20, choices=TransactionTypes.choices)

    direction    = models.CharField(max_length=20, choices=TransactionDirection.choices)
    status       = models.CharField(max_length=30, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    tx_hash      = models.CharField(max_length=255, blank=True, null=True)
    
    counterparty_wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    counterparty_address = models.CharField(max_length=255, blank=True)

    related_transaction = models.OneToOneField(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )

    comment      = models.TextField(blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)

    correlation_id = models.UUIDField(db_index=True, unique=True, null=True, blank=True)

    def __str__(self):
        return f'Transaction #{self.pk}'