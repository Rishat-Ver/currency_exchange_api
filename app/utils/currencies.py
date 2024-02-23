import json
from datetime import date, datetime, timedelta
from functools import wraps

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.httpclientsession import http_client
from app.utils import redis_tool


async def cache_currencies(currencies):
    """Сериализация списка валют для кеширования."""

    currencies_data = json.dumps(currencies)
    # Кешируем на 30 дней
    await redis_tool.set_currency("currencies", currencies_data, expiration=2592000)


async def get_cached_currencies():
    """Получение кешированных данных из Redis."""

    cached = await redis_tool.get_currency("currencies")
    if cached:
        names = json.loads(cached)
        return [code for code in names]
    return None


async def fetch_currency_data():
    """Извлечение кодов валют."""

    cached_currencies = await get_cached_currencies()
    if cached_currencies is not None:
        return cached_currencies
    data = await http_client(url=settings.API.LIST)
    if "currencies" in data:
        cache = {code: country for code, country in data["currencies"].items()}
        await cache_currencies(cache)
        return cache


def check_currencies(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        """Проверка валют на валидность."""

        cache = await redis_tool.get_currency("currencies")
        currencies = [
            code.upper()
            for arg in kwargs.values()
            for code in (arg if isinstance(arg, list) else [arg])
            if isinstance(code, str)
        ]

        if any(currency not in cache for currency in currencies):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect currency code!",
            )
        return await func(*args, **kwargs)

    return wrapper


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
