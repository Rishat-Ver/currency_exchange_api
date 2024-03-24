import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache
from fastapi_limiter.depends import RateLimiter

from app.api.models import User
from app.api.schemas import ResponseCurrency
from app.core.config import settings
from app.services import RedisClient
from app.services.httpclientsession import http_client
from app.utils.currencies import check_currencies, check_time, get_exchange
from app.utils.users import get_current_user

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/exchange_rate", dependencies=[Depends(RateLimiter(times=1, seconds=5))])
@check_currencies
async def get_exchange_rates(
    source: str = Query(default="USD", max_length=3),
    currencies: list[str] = Query(default=None),
    user: User = Depends(get_current_user),
):
    """
    Получает текущие обменные курсы для заданного списка валют относительно указанной базовой валюты.
    Доступен только для авторизованных пользователей.

    Параметры:
    - source: базовая валюта для которой будут получены курсы обмена (по умолчанию "USD").
    - currencies: список целевых валют, для которых необходимо получить курсы обмена.

    Возвращает данные об обменных курсах, включая временную метку обновления данных, базовую валюту и курсы обмена для всех запрошенных валют.
    """

    data = await get_exchange(source=source, currencies=currencies)
    response_data = ResponseCurrency(
        time=datetime.utcfromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        source=data["source"],
        quotes=data["quotes"],
    )

    return response_data


@router.get("/show_convert", dependencies=[Depends(RateLimiter(times=1, seconds=5))])
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


@router.get("/show_change", dependencies=[Depends(RateLimiter(times=1, seconds=5))])
@check_time
@check_currencies
@cache(expire=24 * 60 * 60)
async def show_change(
    start_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    end_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    source: str = "USD",
    currencies: list[str] = Query(
        default=None,
        description="Enter a list of comma-separated currency codes to limit output currencies",
    ),
    user: User = Depends(get_current_user),
):
    """
    Отображает изменение курса валют за указанный период времени между двумя датами для авторизованных пользователей.
    Позволяет пользователю увидеть, как валютный курс менялся в течение времени.

    Параметры:
    - start_date: начальная дата периода (не ранее 1 января 1999 года).
    - end_date: конечная дата периода (не ранее 1 января 1999 года).
    - source: базовая валюта (по умолчанию "USD").
    - currencies: список валют, для которых необходимо получить данные об изменении курса.

    Возвращает данные об изменении курсов валют за указанный период, включая начальную и конечную дату периода.
    """

    param_currency = "%2C".join(currencies) if currencies else ""
    params = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "source": source,
        "currencies": param_currency,
    }
    data = await http_client(url=settings.API.CHANGE, params=params)
    return data


@router.get("/historical", dependencies=[Depends(RateLimiter(times=1, seconds=5))])
@check_time
@check_currencies
@cache(expire=24 * 60 * 60)
async def show_historical(
    historical_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    source: str = "USD",
    currencies: list[str] = Query(
        default=None,
        description="Enter a list of comma-separated currency codes to limit output currencies",
    ),
    user: User = Depends(get_current_user),
):
    """
    Предоставляет исторические курсы валют для указанной даты для авторизованных пользователей.
    Пользователь может запросить курсы обмена на конкретную прошедшую дату для одной или нескольких валют относительно базовой валюты.

    Параметры:
    - historical_date: дата, на которую требуется получить исторические курсы (не ранее 1 января 1999 года).
    - source: базовая валюта (по умолчанию "USD").
    - currencies: список валют, для которых необходимо получить исторические курсы.

    Возвращает исторические курсы валют на указанную дату, включая базовую валюту и курсы для всех запрошенных валют.
    """

    param_currency = "%2C".join(currencies) if currencies else ""
    params = {
        "date": str(historical_date),
        "source": source,
        "currencies": param_currency,
    }
    data = await http_client(url=settings.API.HISTORICAL, params=params)
    return data


@router.get("/list")
async def show_list(
    user: User = Depends(get_current_user),
):
    """
    Возвращает список доступных валют и соответствующих стран для авторизованных пользователей.
    Помогает пользователю узнать, какие валюты доступны для операций в системе.

    Не требует параметров.

    Возвращает список валют в формате код валюты: страна. Этот список может использоваться для выбора валют при выполнении других запросов.
    """
    data = await RedisClient.get_currency("currencies")
    return json.loads(data)


@router.get("/timeframe", dependencies=[Depends(RateLimiter(times=1, seconds=5))])
@check_time
@check_currencies
@cache(expire=300)
async def show_timeframe(
    start_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    end_date: date = Query(
        default=date.today(),
        description="enter the date, no older than January 1, 1999",
    ),
    source: str = "USD",
    currencies: list[str] = Query(
        default=None,
        description="Enter a list of comma-separated currency codes to limit output currencies",
    ),
    user: User = Depends(get_current_user),
):
    """
    Запрашивает курсы валют за определенный период времени для авторизованных пользователей.
    Позволяет пользователю получить информацию о курсах валют на каждую дату в указанном временном промежутке.

    Параметры:
    - start_date: начальная дата периода (не ранее 1 января 1999 года).
    - end_date: конечная дата периода (не ранее 1 января 1999 года).
    - source: базовая валюта (по умолчанию "USD").
    - currencies: список валют, курсы которых требуется получить за период.

    Возвращает данные о курсах валют за каждый день в указанном периоде, позволяя пользователю анализировать динамику изменения курсов.
    """

    param_currency = "%2C".join(currencies) if currencies else ""
    params = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "currencies": param_currency,
        "source": source,
    }
    data = await http_client(url=settings.API.TIMEFRAME, params=params)
    return data
