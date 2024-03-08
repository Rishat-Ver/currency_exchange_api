import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, field_validator, condecimal


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


class CreateUserSchema(UserBase):
    password: str

    @field_validator("password")
    def check_password(cls, v):
        regex = r"(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}"
        if not re.fullmatch(regex, v):
            raise ValueError(
                f"the password must contain more than 8 characters"
                f"and contain Latin letters of different case and numbers"
            )
        return v

    @field_validator("username")
    def check_username(cls, v):
        assert v.isalnum()
        assert v.istitle()
        return v


class ResponseUserBalance(UserBase):
    balances: list[BalanceSchema]
