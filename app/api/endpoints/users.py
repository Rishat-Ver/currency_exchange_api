from fastapi import APIRouter, Depends, status, HTTPException, Query
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User, Balance
from app.api.schemas import CreateUserSchema, BalanceSchema
from app.core.database import get_db_session
from app.services import RedisClient

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


@router.patch("/top_up_balance/")
async def update_balance(
    balance: list[BalanceSchema],
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    cashe = await RedisClient.get_currency("currencies")
    for i in balance:
        if i.currency not in cashe:
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
    return user
