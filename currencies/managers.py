from typing import TypeVar


from django.db import models

T = TypeVar('T')

class CryptoCoinQuerySet(models.QuerySet[T]):
    def with_full_relations(self):
        return self.select_related('parent_coin', 'origin_asset__network').prefetch_related('categories').all()
    
class CryptoCoinManager(models.Manager[T]):
    def get_queryset(self):
        return CryptoCoinQuerySet[T](self.model, using=self._db)
    
    def with_full_relations(self):
        return self.get_queryset().with_full_relations()
    
class BlockchainAssetQuerySet(models.QuerySet[T]):
    def with_network(self):
        return self.select_related('network')
    
class BlockchainAssetManager(models.Manager[T]):
    def get_queryset(self):
        return BlockchainAssetQuerySet[T](self.model, using=self._db)
    
    def with_network(self):
        return self.get_queryset().with_network()