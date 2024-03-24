from datetime import date

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей. Определяет общие атрибуты и методы.
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        """
        Автоматически генерирует имя таблицы для модели, используя имя класса в нижнем регистре и добавляя 's' на конце.
        """
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class Balance(Base):
    """
    Модель для учета баланса пользователя в определенной валюте.
    Содержит информацию о валюте и количестве средств.
    """

    currency: Mapped[str] = mapped_column(default="RUB", server_default="RUB")
    amount: Mapped[Numeric] = mapped_column(
        Numeric(precision=10, scale=2), default=0, server_default="0"
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="balances")


class User(Base):
    """
    Модель пользователя, содержащая основную информацию о пользователе, включая его балансы.
    """

    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[date] = mapped_column(default=date.today)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default="False")
    image_path: Mapped[str] = mapped_column(nullable=True)
    balances = relationship(
        "Balance",
        collection_class=list,
        back_populates="user",
        lazy="selectin",
        cascade="all, delete, delete-orphan",
    )
