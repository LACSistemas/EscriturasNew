"""
FastAPI Users configuration
Configura autenticação JWT (Bearer) e Cookie
"""
import os
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from models.user import User
from auth.user_manager import get_user_manager
from dotenv import load_dotenv

load_dotenv()

# Secret key para JWT (DEVE estar em .env em produção!)
SECRET = os.getenv("SECRET_KEY", "YOUR-SECRET-KEY-CHANGE-IN-PRODUCTION-PLEASE")

# Configurar transporte via Bearer Token (header Authorization: Bearer <token>)
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# Configurar transporte via Cookie (para admin panel HTML)
cookie_transport = CookieTransport(cookie_name="escrituras_auth", cookie_max_age=3600)


def get_jwt_strategy() -> JWTStrategy:
    """Retorna estratégia JWT com tempo de expiração de 1 hora"""
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=3600,  # 1 hora
        token_audience=["fastapi-users:auth"]
    )


# Backend de autenticação JWT (Bearer Token)
auth_backend_jwt = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Backend de autenticação via Cookie (para admin panel)
auth_backend_cookie = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# Instância principal do FastAPIUsers
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend_jwt, auth_backend_cookie],  # Suporta ambos: JWT e Cookie
)

# Dependencies úteis para proteger rotas
current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
