import json

import aiohttp
from fastapi import HTTPException, status

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


async def check_currencies(string: str | None):
    cache = await redis_tool.get_currency("currencies")
    if string:
        string = string.upper()
        currency_list = string.replace(" ", "").split(",")
        if not all(elem in cache for elem in currency_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect currency code!",
            )
        param_currency = (
            "%2C".join(currency_list) if len(currency_list) > 1 else currency_list[0]
        )
        return param_currency
    return ""
