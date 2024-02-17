import json

import aiohttp


from app.api.schemas import Currency
from app.core.config import settings
from app.utils import redis_tool


async def cache_currencies(currencies):
    # Сериализация списка валют для кеширования
    currencies_data = json.dumps([currency.name for currency in currencies])
    # Кешируем на 30 дней
    await redis_tool.set_currency("currencies", currencies_data, expiration=2592000)


async def get_cached_currencies():
    # Получение кешированных данных из Redis
    cached = await redis_tool.get_currency("currencies")
    if cached:
        names = json.loads(cached)
        return [Currency(name=name) for name in names]
    return None


async def fetch_currency_data():
    cached_currencies = await get_cached_currencies()
    if cached_currencies is not None:
        return cached_currencies

    url = settings.API.LIST
    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if "currencies" in data:
                    cache = [Currency(name=name) for name in data["currencies"]]
                    await cache_currencies(cache)
                    return cache
            else:
                print(f"Error {response.status}")
                return None
