# discord_bot/database/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# --- Configuração do Banco de Dados ---
# Por padrão, usamos SQLite para desenvolvimento local.
# Para produção, recomendamos PostgreSQL.

# Para usar PostgreSQL, comente a linha do DATABASE_URL do SQLite
# e descomente a linha do DATABASE_URL do PostgreSQL.
# Lembre-se de configurar as variáveis de ambiente no seu arquivo .env
# com as credenciais do seu banco de dados PostgreSQL.

# --- SQLite ---
DATABASE_URL = "sqlite:///./discord_bot.db"

# --- PostgreSQL ---
# DB_USER = os.getenv("POSTGRES_USER")
# DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
# DB_HOST = os.getenv("POSTGRES_HOST")
# DB_PORT = os.getenv("POSTGRES_PORT")
# DB_NAME = os.getenv("POSTGRES_DB")
# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# --- Engine e Sessão ---
# A engine é o ponto de entrada para o banco de dados.
# O `connect_args` é específico para o SQLite para evitar problemas com threads.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# A sessionmaker cria uma fábrica de sessões.
# Uma sessão é a sua interface para interagir com o banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# A base declarativa é uma classe base para todos os seus modelos do SQLAlchemy.
# Seus modelos herdarão desta classe.
Base = declarative_base()


def create_tables():
    Base.metadata.create_all(bind=engine)


# --- Dependência para obter a sessão do banco de dados ---
def get_db():
    """
    Cria e retorna uma nova sessão do banco de dados.
    Garante que a sessão seja sempre fechada após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
