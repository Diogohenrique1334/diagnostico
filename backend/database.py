# database.py
"""Camada de acesso ao banco — PostgreSQL (Neon) via SQLAlchemy async + asyncpg.

Mesmo padrão de stack do projeto Financas (async). A ponte com o Streamlit
(síncrono) fica em backend/async_runner.py.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

_engine_kwargs = {"echo": settings.DEBUG}

# Configuração de pool só se aplica a backends com pool real (não ao SQLite)
if "sqlite" not in settings.DATABASE_URL:
    _engine_kwargs.update(pool_pre_ping=True)
    # Neon expõe um pooler PgBouncer (host -pooler). Em modo transaction,
    # prepared statements do asyncpg quebram — statement_cache_size=0 resolve.
    _engine_kwargs["connect_args"] = {"statement_cache_size": 0}

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""

    pass


async def create_tables() -> None:
    """Cria todas as tabelas no banco (idempotente)."""
    # Import tardio garante que os modelos estejam registrados no metadata.
    from backend import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
