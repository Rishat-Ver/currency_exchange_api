from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.models import Balance, User
from app.api.schemas import BalanceSchema, CreateUserSchema, ResponseUserBalance
from app.core.database import get_db_session
from app.services import RedisClient
from app.utils.currencies import check_currencies, get_exchange
from app.utils.users import get_current_user

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


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Получение текущего юзера."""

    return user.username


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
            new_balance = Balance(
                amount=balance_item.amount,
                currency=balance_item.currency,
                user_id=user.id,
            )
            session.add(new_balance)

    await session.commit()
    await session.refresh(user)
    response = ResponseUserBalance(
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        balances=[
            BalanceSchema(amount=balance.amount, currency=balance.currency)
            for balance in user.balances
        ],
    )
    return response


@router.patch("/change_currency/")
@check_currencies
async def convert_user_currency(
    source: str,
    currency: str,
    amount: float,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = await session.execute(
        select(User).options(joinedload(User.balances)).where(User.id == user.id)
    )
    res = stmt.scalars().unique().one()

    has_source_currency = [balance.currency for balance in res.balances]
    if source not in has_source_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don`t have this currency",
        )

    has_amount_currency = next(
        (balance.amount for balance in res.balances if balance.currency == source)
    )

    if has_amount_currency < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don`t have enough money on your balance",
        )
    exchange = await get_exchange(source=source, currencies=[currency])
    for balance in res.balances:  # type: Balance
        if balance.currency == source:
            if currency not in has_source_currency:
                new_balance = Balance(
                    amount=exchange["quotes"][f"{source}{currency}"] * amount,
                    currency=currency,
                    user_id=user.id,
                )
                session.add(new_balance)
                balance.amount -= amount
            else:
                change_balance = await session.execute(
                    select(Balance)
                    .options(joinedload(Balance.user))
                    .where(Balance.currency == currency, Balance.user_id == user.id)
                )
                res = change_balance.scalar_one_or_none()
                balance.amount -= amount
                res.amount += exchange["quotes"][f"{source}{currency}"] * amount
        if balance.amount == 0:
            await session.delete(balance)

    await session.commit()
    await session.refresh(user)
    return "успех"
    # {
    #     "success": True,
    #     "timestamp": 1709582583,
    #     "source": "RUB",
    #     "quotes": {"RUBEUR": 0.010051},
    # }
