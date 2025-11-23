"""
Modelo de Templates de Escrituras
Permite que cada usuário customize templates para cada tipo de escritura
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, JSON, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class EscrituraTemplate(Base):
    """
    Template de escritura personalizável por usuário

    Cada usuário pode ter templates customizados para cada tipo de escritura:
    - Lote, Apartamento, Rural, Rural com Desmembramento

    O template é armazenado em JSON com blocos de conteúdo, variáveis e formatação.
    """
    __tablename__ = "escritura_templates"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign Key para User (cada template pertence a um usuário)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tipo de escritura
    tipo_escritura: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo: lote, apto, rural, rural_desmembramento"
    )

    # Dados do Template
    nome_template: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Nome personalizado do template (opcional)"
    )

    # Template JSON - Estrutura com blocos, variáveis, formatação
    template_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="JSON com blocos do template e variáveis usadas"
    )

    # Configurações JSON - Terminologia, formatação, layout
    configuracoes_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON com configurações de terminologia, formatação e layout"
    )

    # Flags
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        comment="Se é o template padrão do usuário para este tipo"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
        comment="Se o template está ativo"
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

    # Constraints
    __table_args__ = (
        # Apenas um template padrão por tipo por usuário
        # Implementado via lógica na API ao invés de constraint DB
        # (para permitir multiple defaults temporariamente durante update)
    )

    def __repr__(self):
        return (
            f"<EscrituraTemplate(id={self.id}, user_id={self.user_id}, "
            f"tipo='{self.tipo_escritura}', default={self.is_default})>"
        )

    @property
    def total_blocos(self) -> int:
        """Retorna número de blocos no template"""
        if self.template_json and "blocos" in self.template_json:
            return len(self.template_json["blocos"])
        return 0

    @property
    def variaveis_usadas(self) -> list:
        """Retorna lista de variáveis usadas no template"""
        if self.template_json and "variaveis_usadas" in self.template_json:
            return self.template_json["variaveis_usadas"]
        return []

    def to_dict(self) -> dict:
        """Converte para dicionário (útil para APIs)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tipo_escritura": self.tipo_escritura,
            "nome_template": self.nome_template,
            "template_json": self.template_json,
            "configuracoes_json": self.configuracoes_json,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total_blocos": self.total_blocos,
            "variaveis_usadas": self.variaveis_usadas
        }
