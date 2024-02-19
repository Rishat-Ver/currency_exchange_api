from datetime import date, datetime

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.models import User
from app.api.schemas import (CurrencyConvert, InfoCurrencyConvert,
                             QueryCurrencyConvert, ResponseCurrency)
from app.core.config import settings
from app.utils.currencies import check_currencies, prepare_exchange_request
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate")
async def get_exchange_rates(
    source: str = Query(default="USD", max_length=3),
    currencies: list[str] = Query(default=None),
    user: User = Depends(get_current_user),
):
    """
    Получение обменных курсов валют.
    Права доступа — авторизованный пользователь.
    """

    source = await check_currencies(source)

    if currencies is not None:
        if len(currencies) == 1 and source == currencies[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data: Currencies and source must be different",
            )
        currencies = [await check_currencies(currency) for currency in currencies]

    url, headers = await prepare_exchange_request(source, currencies)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                response_data = ResponseCurrency(
                    time=datetime.utcfromtimestamp(data["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    source=data["source"],
                    quotes=data["quotes"],
                )
            else:
                response.raise_for_status()
    return response_data


@router.get("/convert")
async def convert(
    amount: float = Query(description="The amount to be converted.", gt=0),
    currency_from: str = Query(
        ...,
        description="Currency you are converting from",
        example="usd",
        min_length=3,
        max_length=3,
    ),
    currency_to: str = Query(
        ...,
        description="Currency you are converting to",
        example="eur",
        min_length=3,
        max_length=3,
    ),
    time: date = date.today(),
    user: User = Depends(get_current_user),
):
    if time > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="unknown exchange rate for the future",
        )
    currency_from = await check_currencies(currency_from)
    currency_to = await check_currencies(currency_to)
    url = "https://api.apilayer.com/currency_data/convert"
    params = {
        "to": currency_to.lower(),
        "from": currency_from.lower(),
        "amount": amount,
        "date": str(time),
    }

    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                data["info"]["date"] = datetime.utcfromtimestamp(
                    data["info"]["timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")
                del data["info"]["timestamp"]
            else:
                response.raise_for_status()
    return data
