from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Balance


async def find_or_create_balance(
    session: AsyncSession, user_id: int, currency: str, amount: Decimal = 0
) -> Balance:
    """Поиск существующего баланса или создание нового."""

    stmt = select(Balance).where(
        Balance.user_id == user_id, Balance.currency == currency
    )
    result = await session.execute(stmt)
    balance = result.scalars().first()
    if not balance:
        balance = Balance(user_id=user_id, currency=currency, amount=amount)
        session.add(balance)
    return balance
