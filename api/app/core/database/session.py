"""Motor SQLAlchemy async único y fábrica de sesiones para toda la aplicación."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config.database_config import db_config

engine = create_async_engine(db_config.url_connection)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por request, cerrada al final."""

    async with async_session_factory() as session:
        yield session
