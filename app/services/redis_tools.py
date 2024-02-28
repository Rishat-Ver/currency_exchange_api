import json

from redis import asyncio as aioredis

from app.core.config import settings
from app.services.httpclientsession import http_client


class RedisClient:
    __redis_connect = aioredis.from_url(
        "redis://localhost:6379", encoding="utf8", decode_responses=True
    )

    @classmethod
    async def set_currency(cls, key, value, expiration=None):
        await cls.__redis_connect.set(key, value, ex=expiration)

    @classmethod
    async def get_currency(cls, key):
        return await cls.__redis_connect.get(key)

    @classmethod
    async def __cache_currencies(cls, currencies):
        """Сериализация списка валют для кеширования."""

        currencies_data = json.dumps(currencies)
        # Кешируем на 30 дней
        await cls.set_currency("currencies", currencies_data, expiration=2592000)

    @classmethod
    async def __get_cached_currencies(cls):
        """Получение кешированных данных из Redis."""

        cached = await cls.get_currency("currencies")
        if cached:
            names = json.loads(cached)
            return [code for code in names]
        return None

    @classmethod
    async def fetch_currency_data(cls):
        """Извлечение кодов валют."""

        cached_currencies = await cls.__get_cached_currencies()
        if cached_currencies is not None:
            return cached_currencies
        data = await http_client(url=settings.API.LIST)
        if "currencies" in data:
            cache = {code: country for code, country in data["currencies"].items()}
            await cls.__cache_currencies(cache)
            return cache
