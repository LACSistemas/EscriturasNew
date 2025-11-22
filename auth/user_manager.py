"""
User Manager para FastAPI Users
Gerencia lifecycle events de usuários (registro, verificação, etc.)
"""
import os
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from models.user import User
from database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Secret key para tokens (DEVE estar em .env em produção!)
SECRET = os.getenv("SECRET_KEY", "YOUR-SECRET-KEY-CHANGE-IN-PRODUCTION-PLEASE")


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    User Manager customizado
    Gerencia eventos de usuário como registro, reset de senha, etc.
    """
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Evento após registro de usuário"""
        logger.info(f"✅ Usuário {user.email} (ID: {user.id}) registrado com sucesso!")
        logger.info(f"⏳ Aguardando aprovação manual do admin para liberar acesso...")

        # Aqui você poderia:
        # - Enviar email para admins notificando novo registro
        # - Enviar email para usuário confirmando registro e informando próximos passos
        # - Logar em sistema de analytics

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Evento após solicitação de reset de senha"""
        logger.info(f"🔑 Usuário {user.email} solicitou reset de senha")
        logger.info(f"Token: {token}")

        # Aqui você enviaria email com link de reset
        # send_password_reset_email(user.email, token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Evento após solicitação de verificação de email"""
        logger.info(f"📧 Usuário {user.email} solicitou verificação de email")
        logger.info(f"Token: {token}")

        # Aqui você enviaria email com link de verificação
        # send_verification_email(user.email, token)

    async def on_after_verify(
        self, user: User, request: Optional[Request] = None
    ):
        """Evento após verificação de email"""
        logger.info(f"✅ Email {user.email} verificado com sucesso!")

    async def on_after_update(
        self,
        user: User,
        update_dict: dict,
        request: Optional[Request] = None,
    ):
        """Evento após atualização de usuário"""
        logger.info(f"🔄 Usuário {user.email} atualizado")

        # Se admin aprovou usuário, logar
        if "is_approved" in update_dict and update_dict["is_approved"]:
            logger.info(f"✅ Usuário {user.email} APROVADO pelo admin!")
            # Aqui você poderia enviar email notificando aprovação
            # send_approval_email(user.email)


# Dependency para obter User Manager
async def get_user_manager(db: AsyncSession = Depends(get_async_db)):
    """Retorna instância do User Manager"""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

    user_db = SQLAlchemyUserDatabase(db, User)
    yield UserManager(user_db)
