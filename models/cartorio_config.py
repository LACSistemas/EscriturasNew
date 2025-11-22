"""
Modelo de configuração de cartório por usuário
Cada usuário pode configurar os dados do cartório que irá assinar as escrituras
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class CartorioConfig(Base):
    """
    Configuração de cartório para cada usuário

    Campos:
    - nome_cartorio: Nome completo do cartório
    - endereco_cartorio: Endereço completo do cartório
    - cidade_cartorio: Cidade do cartório
    - estado_cartorio: Estado do cartório (UF)
    - quem_assina: Nome de quem assina pelo cartório
    """
    __tablename__ = "cartorio_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key para User (1:1 relationship)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Dados do Cartório
    nome_cartorio: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Nome completo do cartório"
    )

    endereco_cartorio: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment="Endereço completo do cartório"
    )

    cidade_cartorio: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Cidade do cartório"
    )

    estado_cartorio: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="Estado do cartório (UF - ex: SP, RJ, MG)"
    )

    quem_assina: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="Nome de quem assina pelo cartório"
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

    # Relationship com User
    # user: Mapped["User"] = relationship("User", back_populates="cartorio_config")

    def __repr__(self):
        return f"<CartorioConfig(id={self.id}, user_id={self.user_id}, cartorio='{self.nome_cartorio}')>"

    @property
    def is_complete(self) -> bool:
        """Verifica se todos os campos obrigatórios foram preenchidos"""
        return all([
            self.nome_cartorio,
            self.endereco_cartorio,
            self.cidade_cartorio,
            self.estado_cartorio,
            self.quem_assina
        ])

    def to_dict(self) -> dict:
        """Converte para dicionário (útil para templates)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nome_cartorio": self.nome_cartorio,
            "endereco_cartorio": self.endereco_cartorio,
            "cidade_cartorio": self.cidade_cartorio,
            "estado_cartorio": self.estado_cartorio,
            "quem_assina": self.quem_assina,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_complete": self.is_complete
        }
