"""Marca un usuario existente como superadmin de plataforma. Es el único
camino para crear el primer superadmin -- no hay endpoint ni UI para esto
a propósito, huevo-y-gallina: el panel de administrador exige ya ser
superadmin para entrar.

Uso: uv run python -B scripts/promote_superadmin.py correo@dominio.com
"""

import asyncio
import sys

from sqlalchemy import update

from app.auth.models.usuario_model import Usuario
from app.core.database.session import async_session_factory


async def _promover(email: str) -> None:
    async with async_session_factory() as session:
        resultado = await session.execute(
            update(Usuario)
            .where(Usuario.email == email.strip().lower())
            .values(es_superadmin=True)
            .returning(Usuario.id)
        )
        if resultado.scalar_one_or_none() is None:
            print(f"No existe ningún usuario con correo {email!r}.")
            raise SystemExit(1)
        await session.commit()
        print(f"{email} ahora es superadmin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: uv run python -B scripts/promote_superadmin.py correo@dominio.com")
        raise SystemExit(1)
    asyncio.run(_promover(sys.argv[1]))
