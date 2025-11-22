"""
User model para autenticação usando FastAPI Users
Extende SQLAlchemyBaseUserTable com campo custom is_approved
"""
from datetime import datetime
from typing import Optional
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    """
    Modelo de usuário com aprovação manual

    Campos padrão do FastAPI Users:
    - id: Integer primary key
    - email: String único
    - hashed_password: String do hash da senha
    - is_active: Boolean se conta está ativa
    - is_superuser: Boolean se é administrador
    - is_verified: Boolean se email foi verificado

    Campo custom:
    - is_approved: Boolean se admin aprovou manualmente
    """
    # Define primary key for integer ID (required when using SQLAlchemyBaseUserTable[int])
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # FastAPI Users já define: email, hashed_password, is_active, is_superuser, is_verified
    # Precisamos adicionar o id e os campos customizados

    # ⚡ CUSTOM FIELD - Aprovação manual do admin
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Relacionamento com sessions de workflow (será criado depois)
    # sessions = relationship("WorkflowSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', approved={self.is_approved}, superuser={self.is_superuser})>"

    @property
    def can_use_escrituras(self) -> bool:
        """Verifica se usuário pode usar o sistema de escrituras"""
        return self.is_active and self.is_approved

    @property
    def can_access_admin(self) -> bool:
        """Verifica se usuário pode acessar painel de administração"""
        return self.is_superuser
