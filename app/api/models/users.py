from datetime import date

from sqlalchemy import func, Enum
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from enum import Enum as PyEnum


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
    created_at: Mapped[date] = mapped_column(server_default=func.today(), default=date.today)
    balance: Mapped[int] = mapped_column(server_default='0', default=0)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), default=Currency.RUB.name, server_default='RUB')
    