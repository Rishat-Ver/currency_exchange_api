from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import Balance


async def find_or_create_balance(
    session: AsyncSession, user_id: int, currency: str, amount: Decimal = 0
) -> Balance:
    """
    Находит существующий баланс пользователя в заданной валюте или создает новый.

    Эта функция ищет в базе данных баланс для указанного пользователя и валюты.
    Если такой баланс найден, он возвращается. Если нет — создается новый баланс
    с начальной суммой, указанной в параметре `amount`, и этот новый баланс возвращается.

    Args:
        session (AsyncSession): Сессия подключения к базе данных для выполнения операций.
        user_id (int): Идентификатор пользователя, для которого проверяется или создается баланс.
        currency (str): Код валюты баланса в формате ISO 4217.
        amount (Decimal, optional): Начальная сумма для нового баланса. По умолчанию равна 0.

    Returns:
        Balance: Найденный или новосозданный объект баланса пользователя.

    Пример использования:
        balance = await find_or_create_balance(session, user_id=1, currency='USD', amount=Decimal('100.00'))
        print(balance.amount)  # Выведет сумму баланса пользователя в USD.
    """

    stmt = select(Balance).where(
        Balance.user_id == user_id, Balance.currency == currency
    )
    result = await session.execute(stmt)
    balance = result.scalars().first()
    if not balance:
        balance = Balance(user_id=user_id, currency=currency, amount=amount)
        session.add(balance)
    return balance
