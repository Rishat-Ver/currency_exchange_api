import json
from datetime import datetime

import aiohttp
from fastapi import APIRouter, HTTPException, status, Depends

from app.api.models import User
from app.api.schemas import ResponseCurrency
from app.core.config import settings


from app.utils import redis_tool
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate")
async def get_exchange_rates(
    source: str = "USD", currencies: str = None, user: User = Depends(get_current_user)
):
    """
    Получение обменных курсов валют.
    Права доступа — авторизованный пользователь.
    """

    if source == currencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currencies must be different",
        )
    cache = await redis_tool.get_currency("currencies")
    print(json.loads(cache))

    currency_list = currencies.replace(" ", "").split(",")

    if not all(elem in cache for elem in currency_list) or source not in cache:
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
