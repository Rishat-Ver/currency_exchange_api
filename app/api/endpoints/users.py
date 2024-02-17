from fastapi import APIRouter, Depends, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas import CreateUserSchema
from app.core.database import get_db_session
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
        balance=user.balance,
        currency=user.currency,
    )
    session.add(new_user)
    await session.commit()
    return new_user


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Получение текущего юзера."""

    return user.username
