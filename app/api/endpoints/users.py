from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.websockets import WebSocket
from fastapi_limiter.depends import RateLimiter
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas import BalanceSchema, CreateUserSchema, ResponseUserBalance
from app.core.database import get_db_session
from app.exceptions import BadRequestException
from app.services import RedisClient
from app.services.websocket_manager import websocket_, ws_manager
from app.utils.balances import find_or_create_balance
from app.utils.currencies import check_currencies, get_exchange
from app.utils.send_email import send_email_async
from app.utils.users import create_response_user_balance, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pass(password: str):
    return pwd_context.hash(password)


@router.websocket("/ws/")
async def websocket_endpoint_users(
    websocket: WebSocket, session=Depends(get_db_session)
):
    await websocket_(websocket, session)


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: CreateUserSchema, session: AsyncSession = Depends(get_db_session)
):
    """
    Создание нового пользователя.
    """

    hash_password = hash_pass(user.password)
    new_user = User(
        username=user.username,
        password=hash_password,
        email=user.email,
    )
    session.add(new_user)
    await session.commit()
    return new_user


@router.get("/me", response_model=ResponseUserBalance)
async def get_me(user: User = Depends(get_current_user)):
    """Получение текущего юзера."""

    response = await create_response_user_balance(user)
    return response


@router.patch("/top_up_balance/", response_model=ResponseUserBalance)
async def update_balance(
    balance: BalanceSchema,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Пополнение баланса пользователем.
    """

    cache = await RedisClient.get_currency("currencies")

    if balance.currency not in cache:
        raise BadRequestException(detail="Incorrect currency")

    existing_balance = next(
        (b for b in user.balances if b.currency == balance.currency), None
    )
    if existing_balance:
        existing_balance.amount += balance.amount
    else:
        await find_or_create_balance(
            session=session,
            user_id=user.id,
            currency=balance.currency,
            amount=balance.amount,
        )

    await session.commit()
    await session.refresh(user)
    background_tasks.add_task(
        send_email_async,
        f"adding funds to your account",
        f"Your balance has been successfully replenished with {balance.amount} {balance.currency}",
        user.email,
    )
    await ws_manager.send_to_user(
        user.id,
        message=f"Your balance has been successfully replenished with {balance.amount} {balance.currency}",
    )
    response = await create_response_user_balance(user)
    return response


@router.patch("/change_currency/", response_model=ResponseUserBalance)
@check_currencies
async def convert_user_currency(
    request: Request,
    background_tasks: BackgroundTasks,
    source: str = Query(
        description="Currency you are converting from",
        example="USD",
        min_length=3,
        max_length=3,
    ),
    currency: str = Query(
        description="Currency you are converting to",
        example="EUR",
        min_length=3,
        max_length=3,
    ),
    amount: float = Query(description="The amount to be converted.", gt=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Конвертирует одну валюту пользователя в другую и отправляет уведомление на почту.

    Параметры:
    - source - валюта, из которой происходит конвертация,
    - currency - валюта, в которую происходит конвертация,
    - amount - количество конвертируемой валюты,

    Возвращает: Пользователя с новым балансом.
    """
    source_balance = next((b for b in user.balances if b.currency == source), None)
    if not source_balance:
        raise BadRequestException(detail="You don't have this currency")

    if source_balance.amount < amount:
        raise BadRequestException(detail="Insufficient funds")

    exchange = await get_exchange(source=source, currencies=[currency])
    exchange_rate = exchange["quotes"][f"{source}{currency}"]

    target_balance = await find_or_create_balance(session, user.id, currency)
    source_balance.amount -= amount
    add_amount = round(amount * exchange_rate, 2)
    target_balance.amount += add_amount

    if source_balance.amount == 0:
        await session.delete(source_balance)

    await session.commit()
    await session.refresh(user)
    background_tasks.add_task(
        send_email_async,
        f"Convert currency",
        f"you exchanged {amount} {source} for {add_amount} {currency}",
        user.email,
    )
    await ws_manager.send_to_user(
        user.id,
        message=f"you exchanged {amount} {source} for {add_amount} {currency}",
    )
    response = await create_response_user_balance(user)
    return response


@router.delete("/me/delete")
async def user_delete(
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Удаление юзера."""

    await session.delete(user)
    await session.commit()
    background_tasks.add_task(
        send_email_async,
        f"delete account",
        f"your account successfully delete",
        user.email,
    )


@router.get(
    "/evaluate_balance", dependencies=[Depends(RateLimiter(times=1, seconds=5))]
)
@check_currencies
async def evaluate_balance_to_only_currency(
    source: str = Query(
        description="Currency you are converting to",
        example="EUR",
        min_length=3,
        max_length=3,
    ),
    user: User = Depends(get_current_user),
):
    """
    Показывает капитал пользователя в валюте source.

    Параметр: source - валюта, в которой будет отражен капитал.

    Возвращает: баланс в валюте source.
    """

    user_currencies = [i.currency for i in user.balances]
    exchange = await get_exchange(source=source, currencies=user_currencies)

    rates_user_currencies = {
        f"{code[3:]}": rate for code, rate in exchange["quotes"].items()
    }

    result = sum(
        balance.amount / rates_user_currencies.get(balance.currency, 1)
        for balance in user.balances
        if balance.currency in rates_user_currencies
        or balance.currency == source.upper()
    )

    return f"Your capital in {source} is {round(result, 2)} {source}"
