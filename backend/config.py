"""Configurações da aplicação via Pydantic BaseSettings.

Fontes da configuração, em ordem de prioridade:
1. Variáveis de ambiente (ex.: Docker / deploy)
2. Arquivo .env na raiz (dev local)
3. st.secrets do Streamlit Community Cloud (fallback)
"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Fallback para Streamlit Community Cloud: lá não há .env; o DATABASE_URL é
# definido em Secrets. O Streamlit costuma expor secrets como variáveis de
# ambiente, mas garantimos copiando para o ambiente caso ainda não esteja.
if "DATABASE_URL" not in os.environ and not _ENV_FILE.exists():
    try:
        import streamlit as st

        for chave in ("DATABASE_URL", "DEBUG"):
            if chave in st.secrets and chave not in os.environ:
                os.environ[chave] = str(st.secrets[chave])
    except Exception:
        # Sem contexto Streamlit / sem secrets (ex.: alembic, scripts): ignora.
        pass


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""

    APP_NAME: str = "Gestão de Diagnósticos"
    DEBUG: bool = False
    DATABASE_URL: str

    class Config:
        env_file = str(_ENV_FILE)
        extra = "allow"


settings = Settings()
