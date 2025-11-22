# 🔐 Guia do Sistema de Autenticação

Sistema completo de autenticação e autorização implementado com FastAPI Users, incluindo painel de administração e integração com Streamlit.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Criar Primeiro Admin](#criar-primeiro-admin)
5. [API Endpoints](#api-endpoints)
6. [Painel de Administração](#painel-de-administração)
7. [Integração Streamlit](#integração-streamlit)
8. [Fluxo de Aprovação](#fluxo-de-aprovação)
9. [Testes](#testes)

---

## Visão Geral

O sistema implementa autenticação completa com:

- ✅ **FastAPI Users** - Framework moderno de autenticação
- ✅ **JWT Tokens** - Autenticação stateless via Bearer tokens
- ✅ **Aprovação Manual** - Admins aprovam novos usuários antes do acesso
- ✅ **Painel Web** - Interface HTML para gerenciar usuários
- ✅ **Proteção de Rotas** - Workflows protegidos por autenticação
- ✅ **Integração Streamlit** - Login integrado no app Streamlit

### Campos do Usuário

Cada usuário possui:

- `id` - ID único (auto-incremento)
- `email` - Email único (usado como username)
- `hashed_password` - Senha criptografada com bcrypt
- `is_active` - Se a conta está ativa
- `is_superuser` - Se é administrador
- `is_verified` - Se o email foi verificado
- **`is_approved`** - ⚡ **Campo custom** - Se admin aprovou o acesso
- `created_at` - Data de criação
- `updated_at` - Data da última atualização

---

## Arquitetura

### Estrutura de Arquivos

```
EscriturasNew/
├── database.py                      # Configuração SQLAlchemy (sync + async)
├── models/
│   ├── user.py                      # Modelo User com campo is_approved
│   └── user_schemas.py              # Pydantic schemas (UserRead, UserCreate, UserUpdate)
├── auth/
│   ├── users.py                     # FastAPI Users setup (JWT strategy)
│   ├── user_manager.py              # UserManager com lifecycle events
│   └── dependencies.py              # Auth dependencies (get_current_approved_user, get_current_admin)
├── routes/
│   ├── admin_routes.py              # API admin (approve, revoke, delete users)
│   └── process_routes_sm.py         # Workflow routes (PROTECTED)
├── templates/
│   └── admin_panel.html             # Painel web de administração
├── scripts/
│   ├── create_admin.py              # Script interativo para criar admin
│   └── create_admin_auto.py         # Script automatizado (para testes)
└── streamlit_login.py               # Módulo de autenticação Streamlit
```

### Fluxo de Dados

```
1. Usuário registra     → POST /auth/register
                          ↓
2. Admin aprova        → PATCH /admin/users/{id}/approve
                          ↓
3. Usuário faz login   → POST /auth/jwt/login → JWT Token
                          ↓
4. Acessa recursos     → GET /users/me (com Bearer token)
                          ↓
5. Usa workflows       → POST /process/sm (protegido)
```

---

## Instalação e Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements_fastapi.txt
```

Pacotes principais:
- `fastapi-users[sqlalchemy]==12.1.2`
- `python-jose[cryptography]==3.3.0`
- `passlib[bcrypt]==1.7.4`
- `sqlalchemy==2.0.23`
- `aiosqlite==0.19.0`

### 2. Configurar Variáveis de Ambiente

Crie `.env`:

```env
# Secret para JWT (MUDE EM PRODUÇÃO!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Database (SQLite para dev, PostgreSQL para prod)
DATABASE_URL=sqlite:///./escrituras.db

# Flask secret (para sessions)
FLASK_SECRET_KEY=your-flask-secret-key
```

### 3. Iniciar Banco de Dados

O banco é criado automaticamente no primeiro startup:

```bash
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000
```

Ou manualmente:

```python
python -c "from database import create_db_and_tables; create_db_and_tables()"
```

---

## Criar Primeiro Admin

### Opção 1: Script Interativo

```bash
python scripts/create_admin.py
```

O script solicitará:
- Email do admin
- Senha (mínimo 8 caracteres)
- Confirmação da senha

### Opção 2: Script Automatizado (Testes)

```bash
python scripts/create_admin_auto.py admin@escrituras.com SenhaSegura123
```

### Verificar Admin Criado

```bash
# Login via API
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@escrituras.com&password=SenhaSegura123"

# Resposta:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

---

## API Endpoints

### Autenticação (FastAPI Users)

#### 1. Registrar Novo Usuário

```bash
POST /auth/register
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "senha123456"
}

# Resposta:
{
  "id": 2,
  "email": "usuario@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "is_approved": false,  # ⚠️ Precisa de aprovação!
  "created_at": "2025-11-22T15:30:00"
}
```

#### 2. Login (Obter JWT Token)

```bash
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=usuario@example.com&password=senha123456

# Resposta:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Obter Dados do Usuário Atual

```bash
GET /users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Resposta:
{
  "id": 2,
  "email": "usuario@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "is_approved": true,
  "created_at": "2025-11-22T15:30:00"
}
```

#### 4. Logout

```bash
POST /auth/jwt/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Admin Endpoints

#### 1. Listar Todos os Usuários (Admin Only)

```bash
GET /admin/users
Authorization: Bearer {admin_token}

# Resposta:
[
  {
    "id": 1,
    "email": "admin@escrituras.com",
    "is_active": true,
    "is_superuser": true,
    "is_verified": true,
    "is_approved": true,
    "created_at": "2025-11-22T14:00:00"
  },
  {
    "id": 2,
    "email": "usuario@example.com",
    "is_active": true,
    "is_superuser": false,
    "is_verified": false,
    "is_approved": false,
    "created_at": "2025-11-22T15:30:00"
  }
]
```

#### 2. Aprovar Usuário (Admin Only)

```bash
PATCH /admin/users/2/approve
Authorization: Bearer {admin_token}

# Resposta:
{
  "success": true,
  "message": "Usuário usuario@example.com aprovado com sucesso",
  "user_id": 2,
  "email": "usuario@example.com",
  "is_approved": true
}
```

#### 3. Revogar Aprovação (Admin Only)

```bash
PATCH /admin/users/2/revoke
Authorization: Bearer {admin_token}

# Resposta:
{
  "success": true,
  "message": "Acesso de usuario@example.com revogado",
  "user_id": 2,
  "email": "usuario@example.com",
  "is_approved": false
}
```

#### 4. Deletar Usuário (Admin Only)

```bash
DELETE /admin/users/2
Authorization: Bearer {admin_token}

# Resposta:
{
  "success": true,
  "message": "Usuário usuario@example.com deletado com sucesso",
  "user_id": 2
}
```

---

## Painel de Administração

### Acessar Painel Web

Abra no navegador:

```
http://localhost:8000/admin/panel
```

⚠️ **Autenticação automática via cookies** - faça login primeiro em `/auth/jwt/login`

### Funcionalidades do Painel

- ✅ **Estatísticas** - Total, aprovados, pendentes, admins
- ✅ **Listagem de Usuários** - Tabela com todos os usuários
- ✅ **Badges de Status** - Visual para aprovado/pendente/admin
- ✅ **Ações Inline** - Aprovar, revogar, deletar
- ✅ **Confirmações** - Diálogos antes de ações destrutivas
- ✅ **Design Moderno** - Interface responsiva e intuitiva

---

## Integração Streamlit

### Uso no `streamlit_app.py`

```python
import streamlit as st
from streamlit_login import check_auth, render_login_page, render_user_info_sidebar

def main():
    """Main application"""

    # 🔐 AUTENTICAÇÃO - Verificar ANTES de qualquer coisa
    if not check_auth():
        # Usuário não autenticado ou não aprovado
        render_login_page()
        return  # Não renderiza o resto do app

    # ✅ Usuário autenticado e aprovado - Continuar com app normal
    init_session_state()
    render_user_info_sidebar()  # Info do usuário na sidebar

    # ... resto do app ...
```

### Funções Disponíveis (`streamlit_login.py`)

#### `check_auth() -> bool`
Verifica se usuário está autenticado E aprovado

```python
if not check_auth():
    render_login_page()
    return
```

#### `render_login_page()`
Renderiza UI de login/registro com tabs

- Tab "Login" - Email + senha
- Tab "Criar Conta" - Email + senha + confirmação

#### `render_user_info_sidebar()`
Mostra info do usuário na sidebar

- Email
- Status de aprovação
- Badge de admin (se aplicável)
- Botão de logout

#### `get_auth_headers() -> Dict[str, str]`
Retorna headers de autenticação para requests

```python
import requests
from streamlit_login import get_auth_headers

response = requests.get(
    "http://localhost:8000/process/sm",
    headers=get_auth_headers()
)
```

#### `is_admin() -> bool`
Verifica se usuário atual é admin

```python
if is_admin():
    st.sidebar.success("👑 Você é administrador!")
```

---

## Fluxo de Aprovação

### 1. Novo Usuário Registra

```python
# Via Streamlit ou API
POST /auth/register
{
  "email": "novo@usuario.com",
  "password": "senha123"
}
```

Resultado:
- ✅ Conta criada
- ⏳ `is_approved = false`
- ❌ Não pode acessar workflows

### 2. Admin Aprova

Via painel web ou API:

```bash
PATCH /admin/users/{id}/approve
```

Resultado:
- ✅ `is_approved = true`
- ✅ Usuário recebe acesso

### 3. Usuário Usa Sistema

Agora o usuário pode:
- ✅ Fazer login
- ✅ Acessar /process/sm
- ✅ Usar todos os workflows
- ✅ Ver informações protegidas

### Fluxograma

```
[Registro] → [Login] → [Bloqueado]
                          ↓
                    [Admin aprova]
                          ↓
              [Login novamente] → [Acesso liberado]
```

---

## Testes

### Teste Completo do Sistema

Execute os seguintes testes para verificar o sistema:

#### 1. Criar Admin

```bash
python scripts/create_admin_auto.py admin@escrituras.com Admin123
```

#### 2. Iniciar API

```bash
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000
```

#### 3. Login Admin

```bash
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@escrituras.com&password=Admin123"
```

Salve o `access_token` retornado.

#### 4. Registrar Usuário Regular

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@user.com","password":"Senha123"}'
```

#### 5. Tentar Acessar Rota Protegida (Deve Falhar)

```bash
# Login do usuário regular
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teste@user.com&password=Senha123"

# Tentar acessar workflow
curl -X POST http://localhost:8000/process/sm \
  -H "Authorization: Bearer {user_token}" \
  -F "response=test"

# Resultado esperado:
# {"detail":"Sua conta ainda não foi aprovada pelo administrador..."}
```

#### 6. Aprovar Usuário

```bash
curl -X PATCH http://localhost:8000/admin/users/2/approve \
  -H "Authorization: Bearer {admin_token}"
```

#### 7. Tentar Acessar Rota Protegida (Deve Funcionar)

```bash
curl -X POST http://localhost:8000/process/sm \
  -H "Authorization: Bearer {user_token}" \
  -F "response=test"

# Resultado esperado: workflow inicia com sucesso
```

### Teste do Streamlit

```bash
# Terminal 1: API
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit
streamlit run streamlit_app.py
```

Acesse `http://localhost:8501` e:

1. Tente acessar sem login → deve mostrar tela de login
2. Crie uma conta → deve criar mas não permitir acesso
3. Faça login → deve mostrar "aguardando aprovação"
4. Aprove via painel admin → `http://localhost:8000/admin/panel`
5. Faça login novamente → deve ter acesso completo

---

## Resumo de Status

### FASE 1: ✅ Sistema de Autenticação FastAPI Users

- ✅ database.py configurado (sync + async)
- ✅ models/user.py com campo is_approved
- ✅ auth/users.py com JWT strategy
- ✅ auth/dependencies.py com proteções custom

### FASE 2: ✅ Painel de Administração Web

- ✅ routes/admin_routes.py com API completa
- ✅ templates/admin_panel.html com interface moderna
- ✅ Estatísticas e ações inline

### FASE 3: ✅ Proteção de Rotas de Workflow

- ✅ routes/process_routes_sm.py protegido
- ✅ Dependência get_current_approved_user
- ✅ Sessões associadas a user_id

### FASE 4: ✅ Integração Streamlit

- ✅ streamlit_login.py com módulo completo
- ✅ streamlit_app.py integrado
- ✅ UI de login/registro

### FASE 5: ✅ Testes Completos

- ✅ Admin criado e testado
- ✅ Fluxo completo de aprovação testado
- ✅ Rotas protegidas funcionando corretamente

---

## Conclusão

Sistema de autenticação completo e testado, pronto para produção com:

- 🔐 Autenticação JWT moderna
- 👑 Painel de administração web
- ✅ Aprovação manual de usuários
- 🛡️ Proteção de rotas sensíveis
- 💻 Integração Streamlit completa

**Próximos Passos (Opcional):**
- Implementar email verification
- Adicionar password reset
- Configurar PostgreSQL para produção
- Implementar rate limiting
- Adicionar logs de auditoria
