# Plan & Tasks: Sistema de Autenticação e Autorização

## 📋 Contexto

Implementar sistema de autenticação usando **FastAPI Users** para controlar acesso à ferramenta de escrituras. Apenas usuários habilitados manualmente pelo admin poderão utilizar o sistema.

## 🎯 Objetivos

1. **Autenticação de Usuários**: Registro e login com email/senha
2. **Aprovação Manual**: Admin habilita/desabilita usuários manualmente
3. **Painel Admin**: Interface web para gerenciar usuários
4. **Proteção de Rotas**: Bloquear acesso à API de escrituras para usuários não habilitados
5. **Integração Streamlit**: Adicionar login no Streamlit app

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                     CAMADA DE APRESENTAÇÃO                   │
├─────────────────────────────────────────────────────────────┤
│  Streamlit App (Login)    │    Admin Panel (Gerenciar Users)│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                       │
├─────────────────────────────────────────────────────────────┤
│  /auth/* (FastAPI Users)  │  /admin/*  │  /api/workflow/*   │
│  - register               │  - list    │  - process_step    │
│  - login                  │  - approve │  - get_session     │
│  - logout                 │  - disable │                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      BANCO DE DADOS                          │
├─────────────────────────────────────────────────────────────┤
│  users (FastAPI Users)    │  sessions (Workflow)            │
│  - id                     │  - session_id                   │
│  - email                  │  - user_id (FK)                 │
│  - hashed_password        │  - current_step                 │
│  - is_active ⚡           │  - data (JSON)                  │
│  - is_approved ⚡ NEW     │  - created_at                   │
│  - is_superuser           │                                 │
│  - created_at             │                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Campos Importantes

- **`is_active`**: Usuário ativou email/conta (FastAPI Users padrão)
- **`is_approved`**: ⚡ **NOVO** - Admin aprovou manualmente (custom field)
- **`is_superuser`**: Usuário admin (pode acessar painel)

**Lógica de Acesso:**
```python
pode_usar_escrituras = user.is_active AND user.is_approved
pode_acessar_admin = user.is_superuser
```

---

## 📦 Tecnologias

| Componente | Tecnologia |
|------------|-----------|
| Autenticação | [FastAPI Users](https://fastapi-users.github.io/fastapi-users/) |
| Database ORM | SQLAlchemy 2.0 |
| Banco de Dados | SQLite (dev) / PostgreSQL (prod) |
| Migrations | Alembic |
| Admin Panel | FastAPI + Jinja2 Templates |
| Streamlit Auth | `streamlit-authenticator` ou requests direto |
| Password Hashing | bcrypt (via FastAPI Users) |
| JWT Tokens | FastAPI Users JWT strategy |

---

## 📝 Tasks Detalhadas

### **FASE 1: Setup FastAPI Users** (Estimativa: 2-3h)

#### Task 1.1: Instalar Dependências
```bash
# Adicionar ao requirements_fastapi.txt
fastapi-users[sqlalchemy]==12.1.2
fastapi-users[jwt]==12.1.2
alembic==1.12.1
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
jinja2==3.1.2
```

#### Task 1.2: Criar Modelo de User
**Arquivo:** `models/user.py`

```python
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.sql import func
from database import Base

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(1024), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # ⚡ CUSTOM FIELD - Aprovação manual do admin
    is_approved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### Task 1.3: Configurar Database
**Arquivo:** `database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./escrituras.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Task 1.4: Configurar FastAPI Users
**Arquivo:** `auth/users.py`

```python
from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from models.user import User
from auth.user_manager import get_user_manager

SECRET = "YOUR-SECRET-KEY-CHANGE-IN-PRODUCTION"  # ⚠️ Mover para .env

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
```

#### Task 1.5: User Manager
**Arquivo:** `auth/user_manager.py`

```python
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from models.user import User
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

SECRET = "YOUR-SECRET-KEY"  # ⚠️ Mover para .env

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered. Waiting for admin approval.")

async def get_user_manager(db: AsyncSession = Depends(get_db)):
    yield UserManager(db)
```

#### Task 1.6: Criar Migrations com Alembic
```bash
# Inicializar Alembic
alembic init alembic

# Criar primeira migration
alembic revision --autogenerate -m "Create users table"

# Aplicar migration
alembic upgrade head
```

#### Task 1.7: Integrar Rotas no FastAPI
**Arquivo:** `main.py` (atualizar)

```python
from fastapi import FastAPI
from auth.users import auth_backend, fastapi_users
from models.user import User

app = FastAPI(title="Sistema de Escrituras")

# Auth routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(User, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(User, UserUpdate),
    prefix="/users",
    tags=["users"],
)
```

---

### **FASE 2: Painel de Administração** (Estimativa: 3-4h)

#### Task 2.1: Criar Dependency para Admin
**Arquivo:** `auth/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from models.user import User
from auth.users import current_active_user

async def get_current_superuser(
    current_user: User = Depends(current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem acessar"
        )
    return current_user

async def get_current_approved_user(
    current_user: User = Depends(current_active_user)
) -> User:
    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sua conta ainda não foi aprovada pelo administrador"
        )
    return current_user
```

#### Task 2.2: Rotas de Administração
**Arquivo:** `routes/admin.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from auth.dependencies import get_current_superuser

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Lista todos os usuários"""
    users = db.query(User).all()
    return users

@router.patch("/users/{user_id}/approve")
async def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Aprovar usuário para usar o sistema"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_approved = True
    db.commit()
    return {"message": f"Usuário {user.email} aprovado"}

@router.patch("/users/{user_id}/revoke")
async def revoke_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Revogar acesso do usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_approved = False
    db.commit()
    return {"message": f"Acesso de {user.email} revogado"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Deletar usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.is_superuser:
        raise HTTPException(status_code=403, detail="Não pode deletar admin")

    db.delete(user)
    db.commit()
    return {"message": f"Usuário {user.email} deletado"}
```

#### Task 2.3: Interface HTML do Painel Admin
**Arquivo:** `templates/admin_panel.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Painel Admin - Escrituras</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .approved { color: green; font-weight: bold; }
        .pending { color: orange; font-weight: bold; }
        .revoked { color: red; font-weight: bold; }
        button { padding: 8px 12px; margin: 2px; cursor: pointer; }
        .approve-btn { background-color: #4CAF50; color: white; }
        .revoke-btn { background-color: #f44336; color: white; }
        .delete-btn { background-color: #555; color: white; }
    </style>
</head>
<body>
    <h1>🔐 Painel de Administração - Usuários</h1>

    <p>Total de usuários: <strong>{{ users|length }}</strong></p>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Ativo</th>
                <th>Aprovado</th>
                <th>Admin</th>
                <th>Criado em</th>
                <th>Ações</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr>
                <td>{{ user.id }}</td>
                <td>{{ user.email }}</td>
                <td>{{ "✅" if user.is_active else "❌" }}</td>
                <td>
                    {% if user.is_approved %}
                        <span class="approved">✅ Aprovado</span>
                    {% else %}
                        <span class="pending">⏳ Pendente</span>
                    {% endif %}
                </td>
                <td>{{ "👑" if user.is_superuser else "" }}</td>
                <td>{{ user.created_at.strftime('%d/%m/%Y %H:%M') }}</td>
                <td>
                    {% if not user.is_superuser %}
                        {% if user.is_approved %}
                            <button class="revoke-btn" onclick="revokeUser({{ user.id }})">
                                Revogar
                            </button>
                        {% else %}
                            <button class="approve-btn" onclick="approveUser({{ user.id }})">
                                Aprovar
                            </button>
                        {% endif %}
                        <button class="delete-btn" onclick="deleteUser({{ user.id }})">
                            Deletar
                        </button>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <script>
        const API_URL = 'http://localhost:8000';
        const token = localStorage.getItem('auth_token');

        async function approveUser(userId) {
            if (!confirm('Aprovar este usuário?')) return;

            const response = await fetch(`${API_URL}/admin/users/${userId}/approve`, {
                method: 'PATCH',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                alert('Usuário aprovado!');
                location.reload();
            } else {
                alert('Erro ao aprovar usuário');
            }
        }

        async function revokeUser(userId) {
            if (!confirm('Revogar acesso deste usuário?')) return;

            const response = await fetch(`${API_URL}/admin/users/${userId}/revoke`, {
                method: 'PATCH',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                alert('Acesso revogado!');
                location.reload();
            } else {
                alert('Erro ao revogar acesso');
            }
        }

        async function deleteUser(userId) {
            if (!confirm('DELETAR este usuário permanentemente?')) return;

            const response = await fetch(`${API_URL}/admin/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                alert('Usuário deletado!');
                location.reload();
            } else {
                alert('Erro ao deletar usuário');
            }
        }
    </script>
</body>
</html>
```

#### Task 2.4: Rota para Servir Painel
**Arquivo:** `routes/admin.py` (adicionar)

```python
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

templates = Jinja2Templates(directory="templates")

@router.get("/panel", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superuser)
):
    """Renderizar painel HTML de administração"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        "admin_panel.html",
        {"request": request, "users": users, "admin": admin}
    )
```

---

### **FASE 3: Proteger Rotas da API** (Estimativa: 1-2h)

#### Task 3.1: Atualizar Rotas de Workflow
**Arquivo:** `routes/workflow.py` (atualizar)

```python
from auth.dependencies import get_current_approved_user

@router.post("/process_step")
async def process_step_endpoint(
    request: ProcessStepRequest,
    current_user: User = Depends(get_current_approved_user)  # ⚡ Proteção
):
    """Processar step do workflow - REQUER APROVAÇÃO"""
    # ... código existente ...
    pass

@router.get("/session/{session_id}")
async def get_session_endpoint(
    session_id: str,
    current_user: User = Depends(get_current_approved_user)  # ⚡ Proteção
):
    """Obter sessão - REQUER APROVAÇÃO"""
    # Verificar se session pertence ao usuário
    # ... código existente ...
    pass
```

#### Task 3.2: Associar Sessions com Users
**Arquivo:** `models/session.py` (atualizar)

```python
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

class WorkflowSession(Base):
    __tablename__ = "workflow_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False)

    # ⚡ NOVO - Associar com usuário
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="sessions")

    current_step = Column(String(255))
    data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

### **FASE 4: Integração com Streamlit** (Estimativa: 2-3h)

#### Task 4.1: Criar Página de Login no Streamlit
**Arquivo:** `streamlit_login.py` (novo)

```python
import streamlit as st
import requests
from typing import Optional

API_URL = "http://localhost:8000"

def login_user(email: str, password: str) -> Optional[dict]:
    """Login via FastAPI"""
    response = requests.post(
        f"{API_URL}/auth/jwt/login",
        data={"username": email, "password": password}
    )

    if response.status_code == 200:
        return response.json()  # {"access_token": "...", "token_type": "bearer"}
    return None

def register_user(email: str, password: str) -> bool:
    """Registrar novo usuário"""
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"email": email, "password": password}
    )
    return response.status_code == 201

def render_login_page():
    """Renderizar página de login"""
    st.title("🔐 Sistema de Escrituras - Login")

    tab1, tab2 = st.tabs(["Login", "Registrar"])

    with tab1:
        st.subheader("Entrar")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")

        if st.button("Entrar", type="primary"):
            if email and password:
                token_data = login_user(email, password)
                if token_data:
                    st.session_state.auth_token = token_data["access_token"]
                    st.session_state.user_email = email
                    st.success("Login realizado!")
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos")
            else:
                st.warning("Preencha todos os campos")

    with tab2:
        st.subheader("Criar Conta")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Senha", type="password", key="register_password")
        password2 = st.text_input("Confirmar Senha", type="password")

        if st.button("Registrar"):
            if password != password2:
                st.error("As senhas não coincidem")
            elif len(password) < 8:
                st.error("Senha deve ter pelo menos 8 caracteres")
            elif email and password:
                if register_user(email, password):
                    st.success("✅ Conta criada! Aguarde aprovação do administrador.")
                    st.info("Você receberá um email quando sua conta for aprovada.")
                else:
                    st.error("Erro ao criar conta. Email já existe?")
            else:
                st.warning("Preencha todos os campos")

def check_auth() -> bool:
    """Verificar se usuário está autenticado e aprovado"""
    if 'auth_token' not in st.session_state:
        return False

    # Verificar se token ainda é válido
    response = requests.get(
        f"{API_URL}/users/me",
        headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
    )

    if response.status_code == 200:
        user_data = response.json()

        # Verificar se foi aprovado
        if not user_data.get("is_approved"):
            st.warning("⏳ Sua conta ainda não foi aprovada pelo administrador.")
            st.info("Entre em contato com o administrador para liberar seu acesso.")
            return False

        return True

    # Token inválido
    del st.session_state.auth_token
    return False
```

#### Task 4.2: Integrar no streamlit_app.py
**Arquivo:** `streamlit_app.py` (início do main)

```python
from streamlit_login import render_login_page, check_auth

def main():
    # Verificar autenticação PRIMEIRO
    if not check_auth():
        render_login_page()
        return

    # ... resto do código existente ...
    init_session_state()
    render_sidebar()
    # etc.
```

---

### **FASE 5: Criar Primeiro Admin** (Estimativa: 30min)

#### Task 5.1: Script para Criar Admin
**Arquivo:** `scripts/create_admin.py`

```python
"""
Script para criar primeiro usuário administrador
Uso: python scripts/create_admin.py
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    # Criar tabelas se não existirem
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    email = input("Email do admin: ")
    password = input("Senha do admin: ")

    # Verificar se já existe
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"❌ Usuário {email} já existe!")
        return

    # Criar admin
    admin = User(
        email=email,
        hashed_password=pwd_context.hash(password),
        is_active=True,
        is_approved=True,  # Admin já aprovado
        is_superuser=True
    )

    db.add(admin)
    db.commit()

    print(f"✅ Admin {email} criado com sucesso!")
    print("Você pode fazer login agora.")

    db.close()

if __name__ == "__main__":
    create_admin()
```

#### Task 5.2: Executar Script
```bash
python scripts/create_admin.py
```

---

### **FASE 6: Testes e Validação** (Estimativa: 2h)

#### Task 6.1: Testar Fluxo Completo
- [ ] Criar admin via script
- [ ] Login como admin no Streamlit
- [ ] Registrar novo usuário normal
- [ ] Acessar painel admin
- [ ] Aprovar usuário normal
- [ ] Login como usuário normal
- [ ] Verificar acesso à ferramenta
- [ ] Revogar usuário
- [ ] Verificar bloqueio de acesso

#### Task 6.2: Testes de Segurança
- [ ] Tentar acessar `/admin/*` sem ser admin → 403
- [ ] Tentar acessar workflow sem aprovação → 403
- [ ] Tentar acessar session de outro usuário → 403
- [ ] Token expirado → 401

#### Task 6.3: Documentação
- [ ] Atualizar README.md com instruções de autenticação
- [ ] Documentar endpoints no Swagger
- [ ] Criar guia de uso do painel admin

---

## 📂 Estrutura de Arquivos Final

```
EscriturasNew/
├── models/
│   ├── user.py              ⚡ NOVO - Modelo de usuário
│   └── session.py           📝 ATUALIZADO - FK para user
├── auth/
│   ├── users.py             ⚡ NOVO - Config FastAPI Users
│   ├── user_manager.py      ⚡ NOVO - User Manager
│   └── dependencies.py      ⚡ NOVO - Auth dependencies
├── routes/
│   ├── admin.py             ⚡ NOVO - Rotas de admin
│   └── workflow.py          📝 ATUALIZADO - Proteger com auth
├── templates/
│   └── admin_panel.html     ⚡ NOVO - Painel HTML
├── scripts/
│   └── create_admin.py      ⚡ NOVO - Criar admin
├── alembic/                 ⚡ NOVO - Migrations
├── database.py              ⚡ NOVO - Config DB
├── streamlit_login.py       ⚡ NOVO - Login Streamlit
├── streamlit_app.py         📝 ATUALIZADO - Integrar auth
├── main.py                  📝 ATUALIZADO - Rotas auth
├── escrituras.db            ⚡ NOVO - SQLite database
└── requirements_fastapi.txt 📝 ATUALIZADO - Deps
```

---

## 🚀 Ordem de Execução

1. ✅ Instalar dependências
2. ✅ Criar models (User)
3. ✅ Configurar database
4. ✅ Setup FastAPI Users
5. ✅ Criar migrations
6. ✅ Criar admin via script
7. ✅ Implementar rotas admin
8. ✅ Criar painel HTML
9. ✅ Proteger rotas workflow
10. ✅ Integrar Streamlit
11. ✅ Testar tudo

---

## ⚠️ Pontos de Atenção

1. **SECRET_KEY**: Mover para variável de ambiente `.env`
   ```bash
   SECRET_KEY=your-super-secret-key-change-in-production
   ```

2. **CORS**: Adicionar para Streamlit acessar API
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:8501"],  # Streamlit
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **HTTPS**: Em produção, usar HTTPS obrigatoriamente

4. **Rate Limiting**: Adicionar para login (evitar brute force)

5. **Email Verification**: Considerar adicionar verificação de email

---

## 📊 Estimativa Total

| Fase | Tempo Estimado |
|------|----------------|
| FASE 1: Setup FastAPI Users | 2-3h |
| FASE 2: Painel Admin | 3-4h |
| FASE 3: Proteger Rotas | 1-2h |
| FASE 4: Streamlit Integration | 2-3h |
| FASE 5: Criar Admin | 30min |
| FASE 6: Testes | 2h |
| **TOTAL** | **11-15 horas** |

---

## ✅ Checklist Final

- [ ] Autenticação funcionando (login/register)
- [ ] Painel admin acessível apenas para superusers
- [ ] Usuários normais bloqueados até aprovação manual
- [ ] Rotas de workflow protegidas
- [ ] Streamlit integrado com login
- [ ] Sessions associadas a usuários
- [ ] Primeiro admin criado
- [ ] Testes de segurança passando
- [ ] Documentação atualizada

---

## 🔗 Referências

- [FastAPI Users Docs](https://fastapi-users.github.io/fastapi-users/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Streamlit Authentication](https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/)
