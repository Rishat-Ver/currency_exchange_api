from datetime import datetime

import aiohttp
from fastapi import APIRouter, HTTPException, status


from app.api.schemas import ResponseCurrency
from app.core.config import settings

from redis import asyncio as aioredis

router = APIRouter(prefix="/currency", tags=["Currency"])

redis = aioredis.from_url(
    "redis://localhost:6379", encoding="utf8", decode_responses=True
)


@router.get("/exchange_rate")
async def get_exchange_rates(source: str = "USD", currencies: str = None):
    cache = await redis.get("currencies")

    currency_list = currencies.split(",")
    if not all(elem in cache for elem in currency_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect currency code!"
        )

    param_currency = (
        "%2C".join(currency_list) if len(currency_list) > 1 else currency_list[0]
    )
    url = f"{settings.API.EXCRATES}?source={source}&currencies={param_currency}"
    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                response = ResponseCurrency(
                    time=datetime.utcfromtimestamp(data["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    source=data["source"],
                    quotes=data["quotes"],
                )

    return response
