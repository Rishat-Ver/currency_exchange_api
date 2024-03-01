from fastapi import APIRouter, Depends, status, HTTPException, Query
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User, Balance
from app.api.schemas import CreateUserSchema
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
    cashe = await RedisClient.get_currency("currencies")

    hash_password = hash_pass(user.password)
    new_user = User(
        username=user.username,
        password=hash_password,
        email=user.email,
    )
    session.add(new_user)
    await session.flush()
    balance_lst = []
    for balance in user.balances:
        if balance.currency not in cashe:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect currency')
        balance_lst.append(Balance(amount=balance.amount, currency=balance.currency, user_id=new_user.id))
    session.add_all(balance_lst)
    await session.commit()
    return new_user


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Получение текущего юзера."""

    return user.username


@router.patch("/top_up_balance/")
async def update_balance(
        balance: float = Query(..., gt=0),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
):
    user.balance += balance
    await session.commit()
    return user
