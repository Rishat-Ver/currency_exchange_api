import json
from datetime import date, datetime, timedelta
from functools import wraps

from fastapi import HTTPException, status

from app.api.schemas import Currency
from app.core.config import settings
from app.services.httpclientsession import http_client
from app.utils import redis_tool


async def cache_currencies(currencies):
    """Сериализация списка валют для кеширования."""

    currencies_data = json.dumps([currency.name for currency in currencies])
    # Кешируем на 30 дней
    await redis_tool.set_currency("currencies", currencies_data, expiration=2592000)


async def get_cached_currencies():
    """Получение кешированных данных из Redis."""

    cached = await redis_tool.get_currency("currencies")
    if cached:
        names = json.loads(cached)
        return [Currency(name=name) for name in names]
    return None


async def fetch_currency_data():
    """Извлечение кодов валют."""

    cached_currencies = await get_cached_currencies()
    if cached_currencies is not None:
        return cached_currencies

    data = await http_client(url=settings.API.LIST)
    if "currencies" in data:
        cache = [Currency(name=name) for name in data["currencies"]]
        await cache_currencies(cache)
        return cache


async def check_currencies(string: str | None):
    """Проверка валют на валидность."""

    cache = await redis_tool.get_currency("currencies")
    if string:
        string = string.upper()
        if string not in cache:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect currency code!",
            )

    return string


def check_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        min_date = date(1999, 1, 1)
        max_date = date.today() - timedelta(hours=3)
        time_lst = [kw for kw in kwargs.values() if isinstance(kw, date)]
        for t in time_lst:
            time = t
            if time < min_date or time > max_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect date",
                )

        return await func(*args, **kwargs)

    return wrapper
