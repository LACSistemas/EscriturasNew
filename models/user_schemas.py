"""
Pydantic schemas para User (FastAPI Users)
Define os schemas para read, create e update de usuários
"""
from fastapi_users import schemas
from pydantic import EmailStr
from typing import Optional
from datetime import datetime


class UserRead(schemas.BaseUser[int]):
    """Schema para leitura de usuário (retornado pela API)"""
    id: int
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    # Custom fields
    is_approved: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Permite criar from ORM models


class UserCreate(schemas.BaseUserCreate):
    """Schema para criação de usuário (registro)"""
    email: EmailStr
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

    # is_approved sempre começa False (precisa aprovação manual)
    is_approved: Optional[bool] = False


class UserUpdate(schemas.BaseUserUpdate):
    """Schema para atualização de usuário"""
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

    # Admin pode atualizar is_approved
    is_approved: Optional[bool] = None
