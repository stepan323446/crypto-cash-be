import requests
from project.settings import EXCHANGE_RATE_KEY, COINGECKO_API_KEY, COINGECKO_IS_PRO
from .types import ExchangeResultSchema, CoingeckoMarketCoin

COINGECKO_API_URL = 'https://pro-api.coingecko.com' if COINGECKO_IS_PRO else 'https://api.coingecko.com'
COINGECKO_HEADER_KEY = 'x-cg-pro-api-key' if COINGECKO_IS_PRO else 'x-cg-demo-api-key'

def get_latest_fiat_currencies():
    response = requests.get(f'https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD')

    if not response.ok:
        raise Exception(f'Unable to retrieve exchange rates. Response code: {response.status_code}')
    
    data = response.json()
    
    return ExchangeResultSchema(**data)

def get_coingecko_markets(coin_ids: list[str]):
    if not coin_ids:
        return

    headers = {
        COINGECKO_HEADER_KEY: COINGECKO_API_KEY
    }
    coin_ids_str = ','.join(coin_ids)
    response = requests.get(
        url=f'{COINGECKO_API_URL}/api/v3/coins/markets?vs_currency=usd&ids={coin_ids_str}&price_change_percentage=7d,14d,30d,1y',
        headers=headers
    )

    if not response.ok:
        raise Exception(f'Unable to retrieve coingecko. Response code: {response.status_code}')
    
    data = response.json()

    return [CoingeckoMarketCoin(**item) for item in data]