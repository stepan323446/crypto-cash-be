from celery import shared_task
from currencies.models import FiatCurrency

from currencies.utils import get_latest_fiat_currencies

@shared_task
def update_fiat_currencies():
    # Get current currencies in local db
    currencies_dict = {c.code: c for c in FiatCurrency.objects.all()}

    # Get currencies by external service api
    exchange_result = get_latest_fiat_currencies()
    exchange_rates = exchange_result.conversion_rates

    # Update exist currencies
    updated_objs = []

    for code, rate in exchange_rates.items():
        if currencies_dict.get(code):
            obj = currencies_dict[code]
            obj.conversion_rate = rate
            updated_objs.append(obj)

    if not updated_objs:
        return {'detail': 'Fiat currencies not updated because not found'}
    
    FiatCurrency.objects.bulk_update(updated_objs, ['conversion_rate', 'time_updated'])

    return {'detail': f'Updated {len(updated_objs)} currencies'}