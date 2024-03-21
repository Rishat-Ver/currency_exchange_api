from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, condecimal


class Token(BaseModel):
    """
    Модель токена доступа, содержащая сам токен и тип токена.
    """

    access_token: str
    token_type: str


class DataToken(BaseModel):
    """
    Модель данных токена, используемая для валидации данных, извлекаемых из токена.
    """

    id: int | None = None


class UserBase(BaseModel):
    """
    Базовая модель пользователя.
    """

    username: str
    email: EmailStr
    created_at: date


class BalanceSchema(BaseModel):
    """
    Схема баланса, представляющая собой баланс пользователя в определенной валюте.
    """

    amount: Decimal = condecimal(gt=Decimal(0))
    currency: str


class ResponseUserBalance(UserBase):
    """
    Модель ответа API для баланса пользователя, содержащая базовую информацию о пользователе и его балансы.
    """

    balances: list[BalanceSchema]
