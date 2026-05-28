# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# URL de conexão com o banco SQLite.
DATABASE_URL = "sqlite:///backend/db/banco_projetos.db"

# Engine de conexão. connect_args é necessário para SQLite em aplicações com threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Fábrica de sessões. A sessão é a forma de interagir com o banco.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função para gerenciar o ciclo de vida da sessão
def get_db_session():
    """
    Cria uma sessão, permite seu uso e garante que ela seja fechada ao final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
