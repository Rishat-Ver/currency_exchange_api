from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column, relationship)


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls):
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)


class Balance(Base):
    currency: Mapped[str] = mapped_column(default="RUB", server_default="RUB")
    amount: Mapped[float] = mapped_column(default=0, server_default="0")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="balances")


class User(Base):
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[date] = mapped_column(default=date.today)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default="False")
    balances = relationship(
        "Balance",
        collection_class=list,
        back_populates="user",
        lazy="selectin",
        cascade="all, delete, delete-orphan",
    )
