from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.security import verify_access_token
from app.api.models import User
from app.api.schemas import BalanceSchema, ResponseUserBalance
from app.core.database import get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login/")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
):
    """Получение текущего юзера."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Failed to verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = verify_access_token(
        token=token, credentials_exception=credentials_exception
    )
    stmt = select(User).where(token.id == User.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    return user


async def create_response_user_balance(user: User) -> ResponseUserBalance:
    """
    Создает и возвращает объект ResponseUserBalance для заданного пользователя.

    :param user: Экземпляр пользователя, для которого необходимо создать ответ.
    :return: Экземпляр ResponseUserBalance с данными пользователя и его балансами.
    """
    return ResponseUserBalance(
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        balances=[
            BalanceSchema(amount=balance.amount, currency=balance.currency)
            for balance in user.balances
        ],
    )
