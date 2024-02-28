from datetime import date, timedelta
from functools import wraps

from fastapi import HTTPException, status

from app.services import RedisClient


def check_currencies(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        """Проверка валют на валидность."""

        cache = await RedisClient.get_currency("currencies")

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
