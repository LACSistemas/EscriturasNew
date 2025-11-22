"""
Rotas para configuração de cartório por usuário
Cada usuário pode gerenciar sua própria configuração de cartório
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_sync_db
from models.user import User
from models.cartorio_config import CartorioConfig
from models.cartorio_schemas import (
    CartorioConfigCreate,
    CartorioConfigUpdate,
    CartorioConfigRead,
    CartorioConfigResponse
)
from auth.dependencies import get_current_approved_user

router = APIRouter(prefix="/cartorio", tags=["cartorio-config"])


@router.get("/config", response_model=CartorioConfigRead)
async def get_cartorio_config(
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🔐 Obter configuração de cartório do usuário atual

    Retorna a configuração de cartório associada ao usuário autenticado.
    Se não existir, retorna 404.
    """
    config = db.query(CartorioConfig).filter(
        CartorioConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de cartório não encontrada. Use POST /cartorio/config para criar."
        )

    return config


@router.post("/config", response_model=CartorioConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_cartorio_config(
    config_data: CartorioConfigCreate,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🔐 Criar configuração de cartório para o usuário atual

    Cria uma nova configuração de cartório. Todos os campos são opcionais
    na criação e podem ser preenchidos posteriormente.

    **Importante**: Cada usuário pode ter apenas UMA configuração.
    """
    # Verificar se já existe configuração para este usuário
    existing = db.query(CartorioConfig).filter(
        CartorioConfig.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Usuário já possui configuração de cartório. Use PUT /cartorio/config para atualizar."
        )

    # Criar nova configuração
    new_config = CartorioConfig(
        user_id=current_user.id,
        nome_cartorio=config_data.nome_cartorio,
        endereco_cartorio=config_data.endereco_cartorio,
        cidade_cartorio=config_data.cidade_cartorio,
        estado_cartorio=config_data.estado_cartorio,
        quem_assina=config_data.quem_assina
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return CartorioConfigResponse(
        success=True,
        message="Configuração de cartório criada com sucesso",
        config=new_config
    )


@router.put("/config", response_model=CartorioConfigResponse)
async def update_cartorio_config(
    config_data: CartorioConfigUpdate,
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🔐 Atualizar configuração de cartório do usuário atual

    Atualiza a configuração existente. Apenas os campos fornecidos serão atualizados.
    Se a configuração não existir, retorna 404.
    """
    config = db.query(CartorioConfig).filter(
        CartorioConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração não encontrada. Use POST /cartorio/config para criar primeiro."
        )

    # Atualizar apenas campos fornecidos (não None)
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return CartorioConfigResponse(
        success=True,
        message="Configuração de cartório atualizada com sucesso",
        config=config
    )


@router.delete("/config", response_model=CartorioConfigResponse)
async def delete_cartorio_config(
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🔐 Deletar configuração de cartório do usuário atual

    Remove completamente a configuração de cartório do usuário.
    """
    config = db.query(CartorioConfig).filter(
        CartorioConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração não encontrada."
        )

    db.delete(config)
    db.commit()

    return CartorioConfigResponse(
        success=True,
        message="Configuração de cartório deletada com sucesso",
        config=None
    )


@router.get("/config/check", response_model=dict)
async def check_config_completeness(
    current_user: User = Depends(get_current_approved_user),
    db: Session = Depends(get_sync_db)
):
    """
    🔐 Verificar se configuração está completa

    Retorna se o usuário tem configuração e se todos os campos obrigatórios
    estão preenchidos.
    """
    config = db.query(CartorioConfig).filter(
        CartorioConfig.user_id == current_user.id
    ).first()

    if not config:
        return {
            "exists": False,
            "is_complete": False,
            "missing_fields": ["Todas as configurações"]
        }

    missing = []
    if not config.nome_cartorio:
        missing.append("Nome do Cartório")
    if not config.endereco_cartorio:
        missing.append("Endereço do Cartório")
    if not config.cidade_cartorio:
        missing.append("Cidade do Cartório")
    if not config.estado_cartorio:
        missing.append("Estado do Cartório")
    if not config.quem_assina:
        missing.append("Quem Assina")

    return {
        "exists": True,
        "is_complete": config.is_complete,
        "missing_fields": missing
    }
