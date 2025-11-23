"""
Pydantic schemas para EscrituraTemplate
Validação de requests e responses da API de templates
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


# ============================================================================
# SCHEMAS DE ESTRUTURA INTERNA (Blocos, Formatação, Configurações)
# ============================================================================

class TemplateBlocoFormatacao(BaseModel):
    """Formatação de um bloco de template"""
    negrito: bool = Field(default=False, description="Texto em negrito")
    italico: bool = Field(default=False, description="Texto em itálico")
    sublinhado: bool = Field(default=False, description="Texto sublinhado")
    alinhamento: str = Field(default="justify", description="Alinhamento: left, center, right, justify")
    tamanho_fonte: Optional[int] = Field(None, description="Tamanho da fonte (opcional)")

    @validator('alinhamento')
    def validate_alinhamento(cls, v):
        """Valida alinhamento"""
        valid = ["left", "center", "right", "justify"]
        if v not in valid:
            raise ValueError(f'Alinhamento deve ser um de: {", ".join(valid)}')
        return v


class TemplateBloco(BaseModel):
    """Bloco de conteúdo do template"""
    id: str = Field(..., description="ID único do bloco")
    tipo: str = Field(..., description="Tipo do bloco (cabecalho, partes, imovel, etc.)")
    ordem: int = Field(..., description="Ordem do bloco no documento")
    conteudo: str = Field(..., description="Conteúdo do bloco (pode conter variáveis [VAR])")
    formatacao: TemplateBlocoFormatacao = Field(default_factory=TemplateBlocoFormatacao)

    @validator('ordem')
    def validate_ordem(cls, v):
        """Valida ordem positiva"""
        if v < 1:
            raise ValueError('Ordem deve ser >= 1')
        return v


class TemplateJSON(BaseModel):
    """Estrutura JSON completa do template"""
    blocos: List[TemplateBloco] = Field(default_factory=list, description="Lista de blocos do template")
    variaveis_usadas: List[str] = Field(default_factory=list, description="Variáveis usadas no template")


class TemplateConfigTerminologia(BaseModel):
    """Configuração de terminologia do template"""
    vendedor: str = Field(default="VENDEDOR", description="Termo para vendedor")
    comprador: str = Field(default="COMPRADOR", description="Termo para comprador")
    imovel: str = Field(default="IMÓVEL", description="Termo para imóvel")


class TemplateConfigFormatacao(BaseModel):
    """Configuração de formatação do template"""
    titulos_negrito: bool = Field(default=True, description="Títulos em negrito")
    variaveis_destacadas: bool = Field(default=True, description="Variáveis destacadas")
    numeracao_automatica: bool = Field(default=True, description="Numeração automática de cláusulas")


class TemplateConfigLayout(BaseModel):
    """Configuração de layout do template"""
    margem_superior: float = Field(default=2.5, description="Margem superior (cm)")
    margem_inferior: float = Field(default=2.5, description="Margem inferior (cm)")
    margem_esquerda: float = Field(default=3.0, description="Margem esquerda (cm)")
    margem_direita: float = Field(default=3.0, description="Margem direita (cm)")
    espacamento_entre_linhas: float = Field(default=1.5, description="Espaçamento entre linhas")
    fonte: str = Field(default="Times New Roman", description="Fonte do documento")
    tamanho_fonte_padrao: int = Field(default=12, description="Tamanho padrão da fonte")


class TemplateConfigJSON(BaseModel):
    """Estrutura JSON completa de configurações"""
    terminologia: TemplateConfigTerminologia = Field(default_factory=TemplateConfigTerminologia)
    formatacao: TemplateConfigFormatacao = Field(default_factory=TemplateConfigFormatacao)
    layout: TemplateConfigLayout = Field(default_factory=TemplateConfigLayout)


# ============================================================================
# SCHEMAS DE API (Create, Update, Read)
# ============================================================================

class TemplateCreate(BaseModel):
    """Schema para criação de template"""
    tipo_escritura: str = Field(..., description="Tipo: lote, apto, rural, rural_desmembramento")
    nome_template: Optional[str] = Field(None, description="Nome personalizado do template")
    template_json: TemplateJSON = Field(..., description="JSON com blocos e variáveis")
    configuracoes_json: Optional[TemplateConfigJSON] = Field(None, description="Configurações opcionais")
    is_default: bool = Field(default=False, description="Se é template padrão para este tipo")

    @validator('tipo_escritura')
    def validate_tipo(cls, v):
        """Valida tipo de escritura"""
        valid = ["lote", "apto", "rural", "rural_desmembramento"]
        if v not in valid:
            raise ValueError(f'Tipo deve ser um de: {", ".join(valid)}')
        return v


class TemplateUpdate(BaseModel):
    """Schema para atualização de template"""
    nome_template: Optional[str] = None
    template_json: Optional[TemplateJSON] = None
    configuracoes_json: Optional[TemplateConfigJSON] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class TemplateRead(BaseModel):
    """Schema para leitura de template"""
    id: int
    user_id: int
    tipo_escritura: str
    nome_template: Optional[str]
    template_json: TemplateJSON
    configuracoes_json: Optional[TemplateConfigJSON]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Para converter de ORM models


class TemplateResponse(BaseModel):
    """Schema de resposta com mensagem"""
    success: bool
    message: str
    template: Optional[TemplateRead] = None


class TemplateListResponse(BaseModel):
    """Schema para lista de templates"""
    success: bool
    total: int
    templates: List[TemplateRead]


# ============================================================================
# SCHEMAS AUXILIARES
# ============================================================================

class TemplatePreviewRequest(BaseModel):
    """Request para preview do template"""
    dados_exemplo: Dict[str, Any] = Field(..., description="Dados de exemplo para substituir variáveis")


class TemplatePreviewResponse(BaseModel):
    """Response do preview"""
    success: bool
    preview_html: str = Field(..., description="HTML renderizado do template")
    preview_text: str = Field(..., description="Texto plano do template")


# ============================================================================
# CONSTANTES
# ============================================================================

# Tipos de escritura válidos
TIPOS_ESCRITURA = ["lote", "apto", "rural", "rural_desmembramento"]

# Tipos de blocos disponíveis
TIPOS_BLOCOS = [
    "cabecalho",
    "identificacao_partes",
    "descricao_imovel",
    "clausulas",
    "valor_pagamento",
    "assinatura",
    "certidoes",
    "rural_especifico",
    "desmembramento"
]
