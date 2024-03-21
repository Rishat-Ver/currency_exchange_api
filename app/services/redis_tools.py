import json

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis

from app.core.config import settings
from app.services.httpclientsession import http_client


class RedisClient:
    """
    Клиент для работы с Redis, обеспечивающий кеширование и ограничение частоты запросов.

    Данный класс использует библиотеку aioredis для асинхронной работы с Redis.
    Предоставляет методы для инициализации кеша и ограничителя частоты запросов в FastAPI,
    а также для установки и получения значений по ключам, специфичным для функционала валют.

    Attributes:
        __redis_connect (Redis): Подключение к Redis.
    """

    __redis_connect = aioredis.from_url(
        "redis://redis:6379", encoding="utf8", decode_responses=True
    )

    @classmethod
    async def fastapi_cache_init(cls):
        """
        Инициализация кеша для FastAPI с использованием Redis.

        Returns:
            FastAPICache: Экземпляр кеша для FastAPI.
        """
        return FastAPICache.init(
            RedisBackend(cls.__redis_connect), prefix="fastapi-cache"
        )

    @classmethod
    async def fastapi_limiter_init(cls):
        """
        Инициализация ограничителя частоты запросов для FastAPI с использованием Redis.

        Returns:
            FastAPILimiter: Экземпляр ограничителя для FastAPI.
        """
        return await FastAPILimiter.init(cls.__redis_connect)

    @classmethod
    async def set_currency(cls, key, value, expiration=None):
        """
        Установка значения по ключу в Redis с опциональным сроком действия.

        Args:
            key (str): Ключ для установки значения.
            value (str): Значение, связанное с ключом.
            expiration (int, optional): Время жизни ключа в секундах.
        """
        await cls.__redis_connect.set(key, value, ex=expiration)

    @classmethod
    async def get_currency(cls, key):
        """
        Получение значения по ключу из Redis.

        Args:
            key (str): Ключ для получения значения.

        Returns:
            str: Значение, связанное с ключом, или None, если ключ не найден.
        """
        return await cls.__redis_connect.get(key)

    @classmethod
    async def __cache_currencies(cls, currencies):
        """
        Сериализация и кеширование списка валют в Redis.

        Args:
            currencies (dict): Словарь кодов валют и соответствующих стран.
        """

        currencies_data = json.dumps(currencies)
        # Кешируем на 30 дней
        await cls.set_currency("currencies", currencies_data, expiration=2592000)

    @classmethod
    async def __get_cached_currencies(cls):
        """
        Получение сериализованного списка валют из кеша Redis.

        Returns:
            list[str]: Список кодов валют, если они были кешированы, иначе None.
        """

        cached = await cls.get_currency("currencies")
        if cached:
            names = json.loads(cached)
            return [code for code in names]
        return None

    @classmethod
    async def fetch_currency_data(cls):
        """
        Извлечение и кеширование кодов валют.

        Сначала проверяет кеш на наличие данных. Если данные отсутствуют, делает запрос
        к внешнему API для получения данных о валютах и кеширует их.

        Returns:
            dict: Словарь кодов валют и соответствующих стран, если запрос успешен.
        """

        cached_currencies = await cls.__get_cached_currencies()
        if cached_currencies is not None:
            return cached_currencies
        data = await http_client(url=settings.API.LIST)
        if "currencies" in data:
            cache = {code: country for code, country in data["currencies"].items()}
            await cls.__cache_currencies(cache)
            return cache
