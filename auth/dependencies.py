"""
Auth Dependencies
Dependencies customizadas para proteger rotas com regras específicas
"""
from fastapi import Depends, HTTPException, status
from models.user import User
from auth.users import current_active_user, current_superuser


async def get_current_approved_user(
    current_user: User = Depends(current_active_user)
) -> User:
    """
    Dependency para obter usuário APROVADO
    Verifica se usuário está ativo E aprovado pelo admin

    Uso:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_approved_user)):
            ...
    """
    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sua conta ainda não foi aprovada pelo administrador. "
                   "Entre em contato com o suporte para liberar seu acesso."
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(current_active_user)
) -> User:
    """
    Dependency para obter usuário ADMIN
    Verifica se usuário é superuser (administrador)

    Uso:
        @router.get("/admin/users")
        async def list_users(admin: User = Depends(get_current_admin)):
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem acessar este recurso"
        )
    return current_user


async def get_current_approved_or_admin(
    current_user: User = Depends(current_active_user)
) -> User:
    """
    Dependency para obter usuário APROVADO OU ADMIN
    Admins sempre podem acessar, mesmo sem aprovação

    Uso:
        @router.get("/some-route")
        async def route(user: User = Depends(get_current_approved_or_admin)):
            ...
    """
    if not current_user.is_superuser and not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Conta não aprovada."
        )
    return current_user
