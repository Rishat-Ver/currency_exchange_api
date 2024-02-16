from redis import asyncio as aioredis


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


redis_tool = RedisClient()
