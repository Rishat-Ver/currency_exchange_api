from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import PyJWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas import DataToken, Token
from app.core.config import settings
from app.core.database import get_db_session

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.AUTH.KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(non_hashed_pass, hashed_pass):
    """
    Проверяет, совпадает ли нехешированный пароль с его хешированной версией.

    :param non_hashed_pass: Нехешированный пароль.
    :param hashed_pass: Хешированный пароль.
    :return: True, если пароли совпадают, иначе False.
    """
    return pwd_context.verify(non_hashed_pass, hashed_pass)


def create_access_token(data: dict):
    """
    Создает JWT токен на основе предоставленных данных.

    :param data: Данные для включения в токен.
    :return: JWT токен.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"expire": expire.strftime("%Y-%m-%d %H:%M:%S")})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    """
    Проверяет JWT токен и извлекает из него данные.

    :param token: JWT токен для проверки.
    :param credentials_exception: Исключение, которое будет вызвано в случае ошибки.
    :return: Данные пользователя из токена.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = DataToken(id=id)
    except PyJWTError as e:
        print(e)
        raise credentials_exception
    return token_data


@router.post("/login/", response_model=Token)
async def login(
    userdetails: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Авторизует пользователя и возвращает токен доступа.

    :param userdetails: Данные пользователя для входа, полученные из формы.
    :param session: Сессия базы данных.
    :return: Токен доступа и тип токена.
    """

    print(userdetails)
    print(userdetails.username, userdetails.password)
    stmt = select(User).filter(userdetails.username == User.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist"
        )
    if not verify_password(userdetails.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "Bearer"}
