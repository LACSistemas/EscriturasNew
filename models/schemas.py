"""Pydantic models for FastAPI request/response validation"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


# Enums for validation
class TipoEscrituraEnum(str, Enum):
    LOTE = "Escritura de Lote"
    APTO = "Escritura de Apto"
    RURAL = "Escritura Rural"
    RURAL_DESMEMBRAMENTO = "Escritura Rural com Desmembramento de Área"


class TipoPessoaEnum(str, Enum):
    FISICA = "Pessoa Física"
    JURIDICA = "Pessoa Jurídica"


class TipoDocumentoEnum(str, Enum):
    IDENTIDADE = "Carteira de Identidade"
    CNH = "CNH"
    CTPS = "Carteira de Trabalho"


# Request models
class ProcessRequest(BaseModel):
    session_id: Optional[str] = None
    response: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class CartorioConfigRequest(BaseModel):
    distrito: str = Field(..., min_length=1)
    municipio: str = Field(..., min_length=1)
    comarca: str = Field(..., min_length=1)
    estado: str = Field(..., min_length=1)
    endereco: str = Field(..., min_length=1)
    quem_assina: str = Field(..., min_length=1)


# Response models
class StepResponse(BaseModel):
    session_id: str
    current_step: str
    question: Optional[str] = None
    options: Optional[List[str]] = None
    requires_file: bool
    progress: str
    file_description: Optional[str] = None
    message: Optional[str] = None
    auto_process: Optional[bool] = None


class ProcessCompleteResponse(BaseModel):
    session_id: str
    status: str
    message: str
    extracted_data: Dict[str, Any]
    escritura: str
    all_extracted_data: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    framework: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Dict[str, str]


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[Dict[str, str]] = None


class CartorioConfigResponse(BaseModel):
    success: bool
    config: Dict[str, str]
    user_id: str


class MessageResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
