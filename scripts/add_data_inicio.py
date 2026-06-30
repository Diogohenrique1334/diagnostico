"""Adiciona a coluna `data_inicio` à tabela `projetos` no Neon (idempotente).

Mesma abordagem do `add_horas_mvp.py`: usada no lugar de uma migration Alembic
porque o histórico do Alembic está desalinhado neste clone. Seguro para rodar
quantas vezes quiser — usa `ADD COLUMN IF NOT EXISTS`.

Uso:
    python scripts/add_data_inicio.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from backend.database import engine  # noqa: E402

_SQL = "ALTER TABLE projetos ADD COLUMN IF NOT EXISTS data_inicio date"
_CHECK = text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'projetos' AND column_name = 'data_inicio'"
)


async def main() -> None:
    async with engine.begin() as conn:
        await conn.execute(text(_SQL))
    async with engine.connect() as conn:
        existe = (await conn.execute(_CHECK)).scalar_one_or_none()
    await engine.dispose()
    if existe:
        print("OK: coluna 'data_inicio' presente em projetos.")
    else:
        print("FALHA: coluna 'data_inicio' não encontrada após o ALTER.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
