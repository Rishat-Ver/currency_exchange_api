import json

import aiohttp
from redis import asyncio as aioredis

from app.api.schemas import Currency
from app.core.config import settings


redis = aioredis.from_url(
    "redis://localhost:6379", encoding="utf8", decode_responses=True
)


async def cache_currencies(currencies):
    # Сериализация списка валют для кеширования
    currencies_data = json.dumps([currency.name for currency in currencies])
    # Кешируем на 30 дней
    await redis.set("currencies", currencies_data, ex=2592000)


async def get_cached_currencies():
    # Получение кешированных данных из Redis
    cached = await redis.get("currencies")
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


# async def main():
#     cached_currencies = await fetch_currency_data()
#     for currency in cached_currencies:
#         print(currency.name)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
