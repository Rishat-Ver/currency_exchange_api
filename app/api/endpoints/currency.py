from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.models import User
from app.api.schemas import ResponseCurrency
from app.core.config import settings
from app.services.httpclientsession import http_client

from app.utils.currencies import check_currencies, check_time
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate")
@check_currencies
async def get_exchange_rates(
    source: str = Query(default="USD", max_length=3),
    currencies: list[str] = Query(default=None),
    user: User = Depends(get_current_user),
):
    """
    Получение обменных курсов валют.
    Права доступа — авторизованный пользователь.
    """

    if currencies is not None:
        if len(currencies) == 1 and source == currencies[0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data: Currencies and source must be different",
            )

    param_currency = "%2C".join(currencies) if currencies else ""
    params = {"source": source, "currencies": param_currency}

    data = await http_client(url=settings.API.EXCRATES, params=params)
    response_data = ResponseCurrency(
        time=datetime.utcfromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        source=data["source"],
        quotes=data["quotes"],
    )

    return response_data


@router.get("/show_convert")
@check_time
@check_currencies
async def show_convert(
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
    time: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    user: User = Depends(get_current_user),
):
    """
    Конвертирует указанную сумму из одной валюты в другую на заданную дату для аутентифицированных пользователей.
    Проверяет валидность входных валют и даты, затем запрашивает курс конвертации через внешний API и возвращает
    результат конвертации.
    """
    # time = validate_date(time)

    params = {
        "to": currency_to.lower(),
        "from": currency_from.lower(),
        "amount": amount,
        "date": str(time),
    }

    data = await http_client(url=settings.API.CONVERT, params=params)
    data["info"]["date"] = datetime.utcfromtimestamp(
        data["info"]["timestamp"]
    ).strftime("%Y-%m-%d %H:%M:%S")
    del data["info"]["timestamp"]

    return data


@router.get("/show_change")
@check_time
@check_currencies
async def show_change(
    start_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    end_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    curriencies: list[str] = Query(
        default=None,
        description="Enter a list of comma-separated currency codes to limit output currencies",
    ),
    source: str = "USD",
):
    params = {
        "to": source.lower(),
        "from": currency_from.lower(),
        "amount": amount,
        "date": str(time),
    }

    data = await http_client(url=settings.API.CONVERT, params=params)
