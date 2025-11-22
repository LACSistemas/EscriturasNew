"""
Pydantic schemas para CartorioConfig
Validação de requests e responses da API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CartorioConfigBase(BaseModel):
    """Schema base com campos comuns"""
    nome_cartorio: Optional[str] = Field(None, max_length=200, description="Nome completo do cartório")
    endereco_cartorio: Optional[str] = Field(None, max_length=300, description="Endereço completo do cartório")
    cidade_cartorio: Optional[str] = Field(None, max_length=100, description="Cidade do cartório")
    estado_cartorio: Optional[str] = Field(None, max_length=2, description="Estado do cartório (UF)")
    quem_assina: Optional[str] = Field(None, max_length=150, description="Nome de quem assina pelo cartório")

    @validator('estado_cartorio')
    def validate_estado(cls, v):
        """Valida que estado é uma UF válida (2 letras maiúsculas)"""
        if v is not None:
            if len(v) != 2:
                raise ValueError('Estado deve ter exatamente 2 caracteres (UF)')
            return v.upper()
        return v


class CartorioConfigCreate(CartorioConfigBase):
    """Schema para criação de configuração de cartório"""
    # Todos os campos são opcionais na criação (podem ser preenchidos depois)
    pass


class CartorioConfigUpdate(CartorioConfigBase):
    """Schema para atualização de configuração de cartório"""
    # Todos os campos são opcionais na atualização (atualiza apenas os fornecidos)
    pass


class CartorioConfigRead(CartorioConfigBase):
    """Schema para leitura de configuração de cartório"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_complete: bool = Field(description="Se todos os campos obrigatórios foram preenchidos")

    class Config:
        from_attributes = True  # Permite criar de ORM models


class CartorioConfigResponse(BaseModel):
    """Schema de resposta com mensagem de sucesso"""
    success: bool
    message: str
    config: Optional[CartorioConfigRead] = None


# Estados brasileiros válidos (para referência)
ESTADOS_VALIDOS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]
