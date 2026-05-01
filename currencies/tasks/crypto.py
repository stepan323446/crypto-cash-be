import time
from celery import shared_task
from django.utils import timezone
from currencies.models import CryptoCoin

from currencies.utils import get_coingecko_markets
from currencies.schemas import PriceHistoryPercentage

@shared_task
def update_crypto_currencies():
    # Get get crypto currencies in local db
    currencies_dict = {c.coingecko_id: c for c in CryptoCoin.objects.all()}
    gecko_coins_ids = list(currencies_dict.keys())

    per_page = 200
    updated_objs = []
    current_time = timezone.now()
    for i in range(0, len(gecko_coins_ids), per_page):
        chunk_ids = gecko_coins_ids[i:i + per_page]

        # Get currencies by external service api
        gecko_coins = get_coingecko_markets(chunk_ids)

        for gk_coin in gecko_coins:
            coin = currencies_dict.get(gk_coin.id)
            if not coin:
                continue

            coin.price = gk_coin.current_price
            coin.change_24h = gk_coin.price_change_percentage_24h
            coin.market_cap = gk_coin.market_cap
            coin.trading_vol_24h = gk_coin.total_volume
            coin.time_updated = current_time

            history = PriceHistoryPercentage()
            history.percentage_7d = gk_coin.price_change_percentage_7d_in_currency
            history.percentage_14d = gk_coin.price_change_percentage_14d_in_currency
            history.percentage_30d = gk_coin.price_change_percentage_30d_in_currency
            history.percentage_1y = gk_coin.price_change_percentage_1y_in_currency

            meta = coin.dynamic_metadata
            meta.price_history = history
            meta.range_24h = (gk_coin.low_24h, gk_coin.high_24h)
            meta.ath = gk_coin.ath
            meta.total_supply = gk_coin.total_supply
            meta.max_supply = gk_coin.max_supply

            coin.set_dynamic_metadata(meta)
            updated_objs.append(coin)

        if len(gecko_coins_ids) > per_page:
            time.sleep(1.5)


    if not updated_objs:
        return {'detail': 'Crypto currencies not updated because not found'}
    
    fields_to_update = ['price', 'change_24h', 'market_cap', 'trading_vol_24h', 'extra_data', 'time_updated']
    CryptoCoin.objects.bulk_update(updated_objs, fields_to_update, batch_size=100)

    return {'detail': f'Updated {len(updated_objs)} currencies'}