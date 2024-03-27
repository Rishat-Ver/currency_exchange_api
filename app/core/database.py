import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

db_url: str = (
    f"postgresql+asyncpg://{settings.DB.USER}:"
    f"{settings.DB.PASSWORD}@{settings.DB.HOST}:"
    f"{settings.DB.PORT}/{settings.DB.NAME}"
)


class DBSessionManager:
    """
    Менеджер сессий базы данных для асинхронного взаимодействия с SQLAlchemy.

    Этот класс отвечает за создание и управление асинхронными сессиями и соединениями с базой данных.
    Он предоставляет контекстные менеджеры для управления жизненным циклом соединений и сессий.

    Атрибуты:
        engine (AsyncEngine): Асинхронный движок SQLAlchemy для взаимодействия с базой данных.
        session_maker (sessionmaker): Фабрика асинхронных сессий SQLAlchemy.

    Методы:
        close(): Асинхронно закрывает соединение с базой данных и уничтожает движок.
        connect(): Асинхронный контекстный менеджер для управления соединениями с базой данных.
        session(): Асинхронный контекстный менеджер для управления сессиями базы данных.
    """

    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def close(self):
        """Асинхронно закрывает движок базы данных и очищает ресурсы."""
        if self.engine is None:
            raise Exception("DatabaseSessionManager не инициализирован")
        await self.engine.dispose()

        self.engine = None
        self.session_maker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Предоставляет асинхронный контекст для соединения с базой данных."""
        if self.engine is None:
            raise Exception("DBSessionManager не инициализирован")

        async with self.engine.begin() as conn:
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Предоставляет асинхронный контекст для работы с сессией базы данных."""
        if self.session_maker is None:
            raise Exception("DBSessionManager не инициализирован")

        session = self.session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DBSessionManager(url=db_url, echo=False)


async def get_db_session():
    """
    Асинхронная функция, предоставляющая сессию базы данных через контекстный менеджер.

    Эта функция предназначена для использования в качестве зависимости в FastAPI
    для обеспечения доступа к сессии базы данных в путях запросов.
    """
    async with sessionmanager.session() as session:
        yield session
