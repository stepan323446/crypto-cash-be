from django.urls import path, include
from .views import (
    FiatCurrencyListView,
    CryptoCoinListView,
    CryptoCoinRetrieveView,
    CryptoCategoryListView,
    CryptoCoinRetrieveByIdView,
    CryptoCoinAdminCreateView,
    CryptoCoinAdminRUDView,
    BlockchainAssetListView,
    CryptoCoinChartView
)

fiat_curr_patterns = [
    path('', FiatCurrencyListView.as_view(), name='fiat-currencies-list')
]
crypto = [
    path('coins/', CryptoCoinListView.as_view(), name='crypto-coins'),
    path('coins/<str:slug>/', CryptoCoinRetrieveView.as_view(), name='crypto-coin'),
    path('coins/<int:pk>/', CryptoCoinRetrieveByIdView.as_view(), name='crypto-coin'),
    path('categories/', CryptoCategoryListView.as_view(), name='crypto-categories'),
    path('blockchain-assets/', BlockchainAssetListView.as_view(), name='blockchain-assets'),
    path('coins-chart/', CryptoCoinChartView.as_view(), name='crypto-chart')
]
crypto_admin = [
    path('coins/', CryptoCoinAdminCreateView.as_view(), name='crypto-coin-create'),
    path('coins/<int:pk>', CryptoCoinAdminRUDView.as_view(), name='crypto-coin-create')
]

urlpatterns = [
    path('v1/', include([
        path('fiat-currencies/', include(fiat_curr_patterns)),
        path('crypto/', include(crypto)),
        path('admin/crypto/', include(crypto_admin))
    ]))
]