import aiohttp

from app.core.config import settings


async def http_client(url: str, params: dict | None = None):
    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                response.raise_for_status()
                return
