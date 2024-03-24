from datetime import date, timedelta
from functools import wraps

from app.core.config import settings
from app.exceptions import BadRequestException
from app.services import RedisClient
from app.services.httpclientsession import http_client


def check_currencies(func):
    """
    Декоратор для проверки валидности валютных кодов.

    Использует Redis кэш для проверки, что все переданные в функцию коды валют
    присутствуют в списке поддерживаемых валют. Если хотя бы один код валюты
    не проходит проверку, будет возбуждено исключение BadRequestException.

    Args:
        func: Асинхронная функция, к которой применяется декоратор.

    Returns:
        Оригинальная функция с применённой проверкой валютных кодов.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        cache = await RedisClient.get_currency("currencies")

        currencies = [
            code.upper()
            for arg in kwargs.values()
            for code in (arg if isinstance(arg, list) else [arg])
            if isinstance(code, str)
        ]

        if any(currency not in cache for currency in currencies):
            raise BadRequestException(detail="Incorrect currency code!")

        return await func(*args, **kwargs)

    return wrapper


def check_time(func):
    """
    Декоратор для проверки корректности переданных дат.

    Убеждается, что все переданные даты в функцию находятся в допустимом
    диапазоне между 1 января 1999 года и текущей датой минус 3 часа. Если
    дата не укладывается в этот диапазон, возбуждается исключение BadRequestException.

    Args:
        func: Асинхронная функция, к которой применяется декоратор.

    Returns:
        Оригинальная функция с применённой проверкой дат.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        min_date = date(1999, 1, 1)
        max_date = date.today() - timedelta(hours=3)
        time_lst = [kw for kw in kwargs.values() if isinstance(kw, date)]
        for t in time_lst:
            time = t

            if time < min_date or time > max_date:
                raise BadRequestException(detail="Incorrect date")

        return await func(*args, **kwargs)

    return wrapper


async def get_exchange(
    source: str,
    currencies: list[str],
):
    """
    Получение текущих обменных курсов для списка валют относительно базовой валюты.

    Совершает HTTP-запрос к внешнему сервису обменных курсов для получения актуальных
    стоимостей конвертации из базовой валюты в целевые. В случае если целевая и базовая
    валюты совпадают, возбуждается BadRequestException.

    Args:
        source: Код базовой валюты в формате ISO 4217.
        currencies: Список кодов целевых валют в формате ISO 4217.

    Returns:
        Словарь с данными об обменных курсах.
    """

    if currencies is not None:
        if len(currencies) == 1 and source == currencies[0]:
            raise BadRequestException(
                detail=f"Invalid data: Currencies and source must be different"
            )

    param_currency = "%2C".join(currencies) if currencies else ""
    params = {"source": source, "currencies": param_currency}

    data = await http_client(url=settings.API.EXCRATES, params=params)

    return data
