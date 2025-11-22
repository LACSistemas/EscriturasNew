"""
Admin Routes - Gerenciamento de Usuários
Rotas protegidas para administradores gerenciarem usuários do sistema
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_sync_db
from models.user import User
from models.user_schemas import UserRead
from auth.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])

# Templates (Jinja2)
templates = Jinja2Templates(directory="templates")


# ============================================================================
# API ENDPOINTS (JSON) - Para consumo via JavaScript/Frontend
# ============================================================================

@router.get("/users", response_model=List[UserRead])
async def list_users(
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    📋 Listar todos os usuários (ADMIN ONLY)

    Retorna lista completa de usuários com todos os campos.
    Apenas administradores podem acessar.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    👤 Obter usuário específico por ID (ADMIN ONLY)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado"
        )
    return user


@router.patch("/users/{user_id}/approve")
async def approve_user(
    user_id: int,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    ✅ Aprovar usuário para usar o sistema (ADMIN ONLY)

    Seta is_approved=True, permitindo o usuário acessar o sistema.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado"
        )

    # Não pode aprovar/desaprovar outro admin
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível modificar status de outro administrador"
        )

    # Aprovar
    user.is_approved = True
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": f"Usuário {user.email} aprovado com sucesso",
        "user_id": user.id,
        "email": user.email,
        "is_approved": user.is_approved
    }


@router.patch("/users/{user_id}/revoke")
async def revoke_user(
    user_id: int,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    ❌ Revogar acesso do usuário (ADMIN ONLY)

    Seta is_approved=False, bloqueando acesso ao sistema.
    O usuário ainda existe, mas não pode usar a ferramenta.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado"
        )

    # Não pode revogar outro admin
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível modificar status de outro administrador"
        )

    # Revogar
    user.is_approved = False
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": f"Acesso de {user.email} revogado com sucesso",
        "user_id": user.id,
        "email": user.email,
        "is_approved": user.is_approved
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    🗑️ Deletar usuário permanentemente (ADMIN ONLY)

    ATENÇÃO: Esta ação é irreversível!
    Remove o usuário completamente do banco de dados.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado"
        )

    # Não pode deletar admin
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível deletar administradores"
        )

    # Não pode deletar a si mesmo
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode deletar sua própria conta"
        )

    email = user.email
    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": f"Usuário {email} deletado com sucesso",
        "deleted_user_id": user_id,
        "deleted_email": email
    }


@router.patch("/users/{user_id}/toggle-active")
async def toggle_active(
    user_id: int,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    🔄 Ativar/Desativar conta do usuário (ADMIN ONLY)

    Toggle is_active: True <-> False
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado"
        )

    # Não pode desativar admin
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível modificar status de outro administrador"
        )

    # Toggle
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    status_text = "ativado" if user.is_active else "desativado"
    return {
        "success": True,
        "message": f"Usuário {user.email} {status_text} com sucesso",
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active
    }


# ============================================================================
# HTML PANEL - Interface Web para Administração
# ============================================================================

@router.get("/panel", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    🎨 Painel HTML de Administração

    Interface web para gerenciar usuários:
    - Listar todos os usuários
    - Aprovar/Revogar acesso
    - Ativar/Desativar contas
    - Deletar usuários
    """
    users = db.query(User).order_by(User.created_at.desc()).all()

    # Estatísticas
    total_users = len(users)
    approved_users = sum(1 for u in users if u.is_approved)
    pending_users = total_users - approved_users
    active_users = sum(1 for u in users if u.is_active)

    return templates.TemplateResponse(
        "admin_panel.html",
        {
            "request": request,
            "users": users,
            "admin": admin,
            "stats": {
                "total": total_users,
                "approved": approved_users,
                "pending": pending_users,
                "active": active_users
            }
        }
    )


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_sync_db),
    admin: User = Depends(get_current_admin)
):
    """
    📊 Estatísticas do sistema (ADMIN ONLY)
    """
    users = db.query(User).all()

    return {
        "total_users": len(users),
        "approved_users": sum(1 for u in users if u.is_approved),
        "pending_approval": sum(1 for u in users if not u.is_approved and not u.is_superuser),
        "active_users": sum(1 for u in users if u.is_active),
        "inactive_users": sum(1 for u in users if not u.is_active),
        "admins": sum(1 for u in users if u.is_superuser),
        "timestamp": datetime.now().isoformat()
    }
