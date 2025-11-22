"""
Database configuration for SQLAlchemy
Configura conexão com SQLite (dev) e PostgreSQL (prod)
"""
import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Database URL - usa SQLite por padrão, mas pode ser configurado via .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./escrituras.db")

# Para uso assíncrono, converter sqlite:// para sqlite+aiosqlite://
if DATABASE_URL.startswith("sqlite://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Engines
# Engine síncrono (para Alembic migrations)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True para debug SQL
)

# Engine assíncrono (para FastAPI Users e operações async)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False  # Set to True para debug SQL
)

# Session makers
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base para models
Base = declarative_base()


# Dependency para obter sessão síncrona (para rotas sync)
def get_sync_db() -> Session:
    """Retorna sessão síncrona para uso em rotas síncronas"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency para obter sessão assíncrona (para FastAPI Users e rotas async)
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Retorna sessão assíncrona para uso com FastAPI Users"""
    async with AsyncSessionLocal() as session:
        yield session


# Função para criar todas as tabelas (usado em dev/testes)
def create_db_and_tables():
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")


# Função assíncrona para criar tabelas (usado em produção)
async def async_create_db_and_tables():
    """Cria todas as tabelas no banco de dados (async)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tabelas criadas com sucesso (async)!")


if __name__ == "__main__":
    # Teste rápido da conexão
    print(f"📊 Database URL: {DATABASE_URL}")
    print(f"📊 Async Database URL: {ASYNC_DATABASE_URL}")
    create_db_and_tables()
