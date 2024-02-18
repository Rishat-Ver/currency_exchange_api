from datetime import datetime

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.models import User
from app.api.schemas import ResponseCurrency
from app.core.config import settings
from app.utils.currencies import check_currencies
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate")
async def get_exchange_rates(
    source: str = Query(default="USD", max_length=3),
    currencies: str = None,
    user: User = Depends(get_current_user),
):
    """
    Получение обменных курсов валют.
    Права доступа — авторизованный пользователь.
    """
    if source == currencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: Currencies and source must be different",
        )
    source = await check_currencies(source)
    currencies = await check_currencies(currencies)
    url = f"{settings.API.EXCRATES}?source={source}&currencies={currencies}"
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


@router.put("/exchange_money")
async def exchange_money(currency: str, user: User = Depends(get_current_user)):
    pass
