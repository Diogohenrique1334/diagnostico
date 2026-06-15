"""Configurações da aplicação via Pydantic BaseSettings.

Carrega variáveis de ambiente do .env na raiz do projeto.
Mesmo padrão adotado no projeto Financas.
"""

from pathlib import Path
from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""

    APP_NAME: str = "Gestão de Diagnósticos"
    DEBUG: bool = False
    DATABASE_URL: str

    class Config:
        env_file = str(_ENV_FILE)
        extra = "allow"


settings = Settings()
