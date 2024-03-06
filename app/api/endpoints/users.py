from fastapi import APIRouter, Depends, HTTPException, status, Query
from passlib.context import CryptContext
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession


from app.api.models import User
from app.api.schemas import BalanceSchema, CreateUserSchema, ResponseUserBalance
from app.core.database import get_db_session
from app.services import RedisClient
from app.utils.balances import find_or_create_balance
from app.utils.currencies import check_currencies, get_exchange
from app.utils.users import get_current_user, create_response_user_balance

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pass(password: str):
    return pwd_context.hash(password)


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
    balance: list[BalanceSchema],
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Пополнение баланса пользователем.
    """

    cache = await RedisClient.get_currency("currencies")
    for i in balance:
        if i.currency not in cache:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect currency"
            )

    for balance_item in balance:
        existing_balance = next(
            (b for b in user.balances if b.currency == balance_item.currency), None
        )
        if existing_balance:
            existing_balance.amount += balance_item.amount
        else:
            await find_or_create_balance(
                session=session,
                user_id=user.id,
                currency=balance_item.currency,
                amount=balance_item.amount,
            )

    await session.commit()
    await session.refresh(user)
    response = await create_response_user_balance(user)
    return response


@router.patch("/change_currency/", response_model=ResponseUserBalance)
@check_currencies
async def convert_user_currency(
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
    source_balance = next((b for b in user.balances if b.currency == source), None)
    if not source_balance:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="You don't have this currency"
        )

    if source_balance.amount < amount:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

    exchange = await get_exchange(source=source, currencies=[currency])
    exchange_rate = exchange["quotes"][f"{source}{currency}"]

    target_balance = await find_or_create_balance(session, user.id, currency)
    source_balance.amount -= amount
    target_balance.amount += amount * exchange_rate

    if source_balance.amount == 0:
        await session.delete(source_balance)

    await session.commit()
    await session.refresh(user)

    response = await create_response_user_balance(user)
    return response


@router.delete("/me/delete")
async def user_delete(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Удаление юзера."""

    await session.delete(user)
    await session.commit()
