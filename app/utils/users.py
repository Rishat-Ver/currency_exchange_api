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
    """
    Получает текущего пользователя из токена аутентификации.

    Args:
        token (str): Токен аутентификации пользователя.
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        User: Экземпляр пользователя, аутентифицированного токеном.

    Raises:
        HTTPException: Если аутентификация не удалась.
    """

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
    Создает объект ответа с информацией о балансе пользователя.

    Args:
        user (User): Экземпляр пользователя, для которого создается ответ.

    Returns:
        ResponseUserBalance: Объект ответа с информацией о балансе пользователя.
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
    """
    Получает пользователя, ассоциированного с токеном из WebSocket соединения.

    Args:
        websocket (WebSocket): WebSocket соединение.
        session (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        User: Экземпляр пользователя, аутентифицированного через WebSocket.

    Raises:
        WebSocketException: Если аутентификация не удалась.
    """
    token = websocket.headers.get("authorization").split("Bearer ")[1]
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    user = await get_current_user(token, session)
    if not user:
        raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED)
    return user


def check_password_and_username(func):
    """
    Декоратор для валидации имени пользователя и пароля.

    Проверяет, что имя пользователя состоит только из буквенно-цифровых символов,
    начинается с заглавной буквы, и что пароль соответствует заданным критериям
    безопасности (не менее 8 символов, содержит заглавные и строчные буквы, а также цифры).

    Args:
        func (Callable): Функция, к которой применяется декоратор.

    Returns:
        Callable: Обертка над функцией с дополнительной логикой валидации.
    """

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
