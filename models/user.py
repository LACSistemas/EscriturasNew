"""
User model para autenticação usando FastAPI Users
Extende SQLAlchemyBaseUserTable com campo custom is_approved
"""
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    __tablename__ = "users"

    # FastAPI Users já define: id, email, hashed_password, is_active, is_superuser, is_verified
    # Precisamos apenas adicionar os campos customizados

    # ⚡ CUSTOM FIELD - Aprovação manual do admin
    is_approved = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Se TRUE, admin aprovou usuário manualmente para usar o sistema"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Data de criação do usuário"
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Data da última atualização"
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
