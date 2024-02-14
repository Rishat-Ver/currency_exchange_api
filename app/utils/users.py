from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.security import verify_access_token
from app.api.models import User
from app.core.database import get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login/")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
):
    """Получение текущего юзера."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Failed to verify credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = verify_access_token(
        token=token, credentials_exception=credentials_exception
    )
    stmt = select(User).where(token.id == User.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    return user