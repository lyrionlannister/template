"""La app debe poder conectarse a PostgreSQL real a través de la fábrica de
sesiones única del núcleo."""

from sqlalchemy import text

from app.core.database.session import async_session_factory


async def test_sesion_ejecuta_consulta_contra_postgres_real():
    async with async_session_factory() as session:
        resultado = await session.execute(text("select 1"))
        assert resultado.scalar_one() == 1
