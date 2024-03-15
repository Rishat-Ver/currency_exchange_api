from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, condecimal


class Token(BaseModel):
    access_token: str
    token_type: str


class DataToken(BaseModel):
    id: int | None = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    created_at: date


class BalanceSchema(BaseModel):
    amount: Decimal = condecimal(gt=Decimal(0))
    currency: str


class ResponseUserBalance(UserBase):
    balances: list[BalanceSchema]
