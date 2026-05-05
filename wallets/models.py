import uuid
from decimal import Decimal

from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

from currencies.models import BlockchainAsset
from users.models import User

# Create your models here.
class Wallet(models.Model):
    asset        = models.ForeignKey(BlockchainAsset, on_delete=models.PROTECT)
    balance      = models.DecimalField(max_digits=36, decimal_places=18, default=0)

    holder_type  = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    holder_id    = models.PositiveBigIntegerField(db_index=True)
    holder_object = GenericForeignKey("holder_type", "holder_id")

    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'holder_id', 'holder_type', 'asset')

    @property
    def balance_usd(self):
        return self.balance * self.asset.coin.price
    
    @property
    def change_24h(self):
        return self.balance_usd * self.asset.coin.change_24h
    
    @classmethod
    def get_create_wallet_by_user(cls, user: User, asset: BlockchainAsset, holder_model = None, holder_id = None):
        model = holder_model if holder_model else User
        ctype = ContentType.objects.get_for_model(model)
        holder_id = holder_id if holder_id is not None else user.pk

        return cls.objects.get_or_create(
            asset=asset,
            user=user,
            holder_type=ctype,
            holder_id=holder_id
        )
    
    @classmethod
    def get_locked_wallets(cls, *wallets: "Wallet"):
        wallet_ids = sorted([w.pk for w in wallets])
        
        locked_wallets = list(Wallet.objects.select_for_update().filter(pk__in=wallet_ids))

        w_map = {w.pk: w for w in locked_wallets}

        return [w_map[w.pk] for w in wallets]
    
    @classmethod
    def deposit(cls, 
                user: User, amount: Decimal, asset: BlockchainAsset, counterparty_address: str, tx_hash: str,
                fee = Decimal(0), holder_model = None, holder_id = None, message: str = None):
        if amount <= 0 or fee <= 0:
            raise ValidationError('Amount and Fee must be greater than 0')

        with transaction.atomic():
            target_wallet, created = cls.get_create_wallet_by_user(
                user,
                asset,
                holder_model,
                holder_id
            )
            locked_wallet = cls.objects.select_for_update().get(pk=target_wallet.pk)
            locked_wallet.balance += amount
            locked_wallet.save()

            price_at_time = asset.coin.get_price_amount(amount)

            transaction_wallet = Transaction(
                wallet=locked_wallet,
                amount=amount,
                fee=fee * -1,
                price_at_time=price_at_time,
                tx_type=Transaction.TransactionTypes.DEPOSIT,
                direction=Transaction.TransactionDirection.EXTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                counterparty_address=counterparty_address,
                tx_hash=tx_hash,
                message=message
            )
            transaction_wallet.save()

    @classmethod
    def withdraw(cls, user: User, amount: Decimal, asset: BlockchainAsset, counterparty_address: str, tx_hash: str, 
                 fee = Decimal(0), holder_model = None, holder_id = None, message: str = None):
        if amount <= 0 or fee <= 0:
            raise ValidationError('Amount and Fee must be greater than 0')
        
        system_user = User.get_system_user()
        
        correlation_id = uuid.uuid4()
        
        with transaction.atomic():
            target_wallet, created = cls.get_create_wallet_by_user(
                user,
                asset,
                holder_model,
                holder_id
            )
            system_wallet, created = cls.get_create_wallet_by_user(
                system_user,
                asset
            )
            locked_wallet, locked_system_wallet = cls.get_locked_wallets(target_wallet, system_wallet)

            total_amount = amount + fee

            if locked_wallet.balance < total_amount:
                raise ValidationError("Insufficient funds for withdrawal and fee")

            locked_wallet.balance -= total_amount
            locked_system_wallet.balance += fee

            Wallet.objects.bulk_update([locked_wallet, locked_system_wallet], fields=['balance'])

            price_at_time = asset.coin.get_price_amount(amount)

            transaction_wallet = Transaction(
                wallet=locked_wallet,
                amount=amount * -1,
                fee=fee * -1,
                price_at_time=price_at_time,
                tx_type=Transaction.TransactionTypes.WITHDRAW,
                direction=Transaction.TransactionDirection.EXTERNAL,
                status=Transaction.TransactionStatus.PENDING,
                counterparty_address=counterparty_address,
                tx_hash=tx_hash,
                correlation_id=correlation_id,
                message=message
            )
            system_fee_transaction = Transaction(
                wallet=locked_system_wallet,
                amount=fee,
                price_at_time=price_at_time,
                tx_type=Transaction.TransactionTypes.FEE_REVENUE,
                direction=Transaction.TransactionDirection.INTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                counterparty_wallet=locked_wallet,
                correlation_id=correlation_id,
            )
            Transaction.objects.bulk_create([transaction_wallet, system_fee_transaction])

    def transfer_to_wallet(self, to_wallet: "Wallet", amount: Decimal, message: str = None):
        if to_wallet.asset != self.asset:
            raise ValidationError('Cannot transfer between different assets.')
        
        if to_wallet.user == self.user:
            raise ValidationError('Cannot transfer yourself')
        
        if amount <= 0:
            raise ValidationError('Amount must be greater than 0')
        
        correlation_id = uuid.uuid4()
        # Atomicity
        with transaction.atomic():
            # Deadlock and Race condition
            self_locked, to_locked = self.get_locked_wallets(self, to_wallet)

            if self_locked.balance < amount:
                raise ValidationError('Insufficient funds.')
            
            self_locked.balance -= amount
            to_locked.balance += amount
            Wallet.objects.bulk_update([self_locked, to_locked], ['balance'])

            price_at_time = self.asset.coin.get_price_amount(amount)

            transaction_wallet = Transaction(
                wallet=self_locked,
                amount=amount * -1,
                price_at_time=price_at_time * -1,
                tx_type=Transaction.TransactionTypes.TRANSFER,
                direction=Transaction.TransactionDirection.INTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                counterparty_wallet=to_locked,
                correlation_id=correlation_id,
                message=message
            )
            transaction_to_wallet = Transaction(
                wallet=to_locked,
                amount=amount,
                price_at_time=price_at_time,
                tx_type=Transaction.TransactionTypes.TRANSFER,
                direction=Transaction.TransactionDirection.INTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                counterparty_wallet=self_locked,
                correlation_id=correlation_id,
                message=message
            )
            Transaction.objects.bulk_create([transaction_wallet, transaction_to_wallet])

    def transfer_to_user(self, to_user: User, amount: Decimal, holder_model = None, holder_id = None, message: str = None):
        with transaction.atomic():     
            target_wallet, created = self.get_create_wallet_by_user(
                to_user,
                self.asset,
                holder_model,
                holder_id,
            )
            
            return self.transfer_to_wallet(target_wallet, amount, message)
    
    @classmethod
    def manual_adjustment(cls, to_user: User, amount: Decimal, asset: BlockchainAsset, reason: str, holder_model=None, holder_id=None):
        with transaction.atomic():
            target_wallet, created = cls.get_create_wallet_by_user(
                to_user, asset, holder_model, holder_id
            )
            
            locked_wallet = cls.objects.select_for_update().get(pk=target_wallet.pk)
            locked_wallet.balance += amount
            locked_wallet.save()

            price_at_time = asset.coin.get_price_amount(abs(amount))

            transaction_record = Transaction(
                wallet=locked_wallet,
                amount=amount,
                price_at_time=price_at_time,
                tx_type=Transaction.TransactionTypes.ADJUSTMENT,
                direction=Transaction.TransactionDirection.INTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                comment=reason
            )
            transaction_record.save()

    def __str__(self):
        return f'Holder {self.holder_object} - {self.asset.coin.name} ({self.asset.network})'

class Transaction(models.Model):
    class TransactionTypes(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAW = 'withdraw', 'Withdraw'
        TRANSFER = 'transfer', 'Transfer'
        PAYMENT = 'payment', 'Payment'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        FEE_REVENUE = 'fee_revenue', 'Fee Revenue'

    class TransactionDirection(models.TextChoices):
        INTERNAL = 'internal', 'Internal'
        EXTERNAL = 'external', 'External'

    class TransactionStatus(models.TextChoices):
        SUCCESS = 'success', 'Success'
        PENDING = 'pending', 'Pending'
        DENIED = 'denied', 'Denied'

    wallet       = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount       = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    fee          = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    price_at_time = models.DecimalField(max_digits=18, decimal_places=2, help_text="Price at time with USD for coin")
    tx_type      = models.CharField(max_length=20, choices=TransactionTypes.choices)

    direction    = models.CharField(max_length=20, choices=TransactionDirection.choices)
    status       = models.CharField(max_length=30, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    tx_hash      = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    counterparty_wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    counterparty_address = models.CharField(max_length=255, blank=True)

    comment      = models.TextField(blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)

    correlation_id = models.UUIDField(db_index=True, null=True, blank=True)

    def refund_transaction(self, comment: str = None):
        if self.status != self.TransactionStatus.PENDING:
            raise ValidationError('Refund amount can be used only for PENDING transactions')
        
        system_user = User.get_system_user()

        with transaction.atomic():
            system_wallet, created = Wallet.get_create_wallet_by_user(
                system_user,
                self.wallet.asset
            )
                
            locked_wallet, locked_system_wallet = Wallet.get_locked_wallets(self.wallet, system_wallet)
            
            return_amount = abs(self.amount) + abs(self.fee)

            locked_wallet.balance += return_amount
            locked_wallet.save()

            locked_system_wallet.balance -= abs(self.fee)
            locked_system_wallet.save()

            system_fee_refund = Transaction(
                wallet=locked_system_wallet,
                amount=abs(self.fee),
                price_at_time=self.price_at_time,
                tx_type=Transaction.TransactionTypes.ADJUSTMENT,
                direction=Transaction.TransactionDirection.INTERNAL,
                status=Transaction.TransactionStatus.SUCCESS,
                counterparty_wallet=locked_wallet,
                correlation_id=self.correlation_id,
            )
            system_fee_refund.save()

            self.status = self.TransactionStatus.DENIED
            self.comment = comment
            self.save()

    def __str__(self):
        return f'Transaction #{self.pk}'