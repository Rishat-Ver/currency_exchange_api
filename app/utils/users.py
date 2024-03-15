import re
from functools import wraps

from fastapi import Depends, HTTPException, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.websockets import WebSocket
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


async def get_user_with_token(websocket: WebSocket, session: AsyncSession):
    token = websocket.headers.get("authorization").split("Bearer ")[1]
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = await get_current_user(token, session)
    if not user:
        raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED)
    return user


def check_password_and_username(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        regex = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}"
        if kwargs["username"]:
            try:
                assert kwargs["username"].isalnum()
                assert kwargs["username"].istitle()
            except AssertionError as error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Все плохо"
                )
        if kwargs["password"]:
            if not re.fullmatch(regex, kwargs["password"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"the password must contain more than 8 characters"
                    f"and contain Latin letters of different case and numbers",
                )
        return await func(*args, **kwargs)

    return wrapper


# @field_validator("password")
#     def check_password(cls, v):
#         regex = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}"
#         if not re.fullmatch(regex, v):
#             raise ValueError(
#                 f"the password must contain more than 8 characters"
#                 f"and contain Latin letters of different case and numbers"
#             )
#         return v
#
#     @field_validator("username")
#     def check_username(cls, v):
#         assert v.isalnum()
#         assert v.istitle()
#         return v
