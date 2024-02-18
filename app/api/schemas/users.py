import re
from datetime import date

from pydantic import BaseModel, EmailStr, NonNegativeFloat, field_validator, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class DataToken(BaseModel):
    id: int | None = None


class UserBase(BaseModel):
    username: str
    email: EmailStr
    created_at: date


class CreateUserSchema(UserBase):
    password: str
    balance: NonNegativeFloat = 0
    currency: str = Field(
        default="RUB",
        max_length=3,
    )

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


class GetUsersSchema(UserBase):
    balance: NonNegativeFloat = 0
    currency: str = "RUB"
