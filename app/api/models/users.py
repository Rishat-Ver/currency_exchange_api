from datetime import date
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Numeric
from sqlalchemy.dialects.postgresql import BIGINT
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column)


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class Currency(PyEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    YEN = "YEN"
    GBR = "GBR"
    CNY = "CNY"


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[date] = mapped_column(default=date.today)
    balance: Mapped[float] = mapped_column(server_default="0", default=0)
    currency: Mapped[str] = mapped_column(server_default="RUB", default="RUB")
