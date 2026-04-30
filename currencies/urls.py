from django.urls import path, include
from .views import FiatCurrencyListView

fiat_curr_patterns = [
    path('', FiatCurrencyListView.as_view(), name='fiat-currencies-list')
]

urlpatterns = [
    path('v1/', include([
        path('fiat-currencies/', include(fiat_curr_patterns)),
    ]))
]