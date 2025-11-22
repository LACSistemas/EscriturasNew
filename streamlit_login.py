"""
Streamlit Login Module
Integração com FastAPI Users para autenticação no Streamlit
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# URL da API (pode ser configurada via environment)
API_URL = "http://localhost:8000"


# ============================================================================
# API Functions
# ============================================================================

def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Login via FastAPI Users

    Returns:
        dict com 'access_token' e 'token_type' se sucesso
        None se falhar
    """
    try:
        response = requests.post(
            f"{API_URL}/auth/jwt/login",
            data={
                "username": email,  # FastAPI Users usa 'username' no form
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            return response.json()  # {"access_token": "...", "token_type": "bearer"}
        else:
            logger.warning(f"Login failed for {email}: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Login error: {e}")
        return None


def register_user(email: str, password: str) -> tuple[bool, Optional[str]]:
    """
    Registrar novo usuário

    Returns:
        (success: bool, error_message: Optional[str])
    """
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": email,
                "password": password
            }
        )

        if response.status_code == 201:
            return True, None
        else:
            error_data = response.json()
            error_msg = error_data.get("detail", "Erro ao criar conta")
            return False, error_msg

    except Exception as e:
        logger.error(f"Register error: {e}")
        return False, str(e)


def get_current_user(token: str) -> Optional[Dict[str, Any]]:
    """
    Obter dados do usuário atual via token

    Returns:
        dict com dados do usuário se válido
        None se token inválido
    """
    try:
        response = requests.get(
            f"{API_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception as e:
        logger.error(f"Get user error: {e}")
        return None


def logout_user(token: str) -> bool:
    """
    Logout (invalida token no backend)

    Returns:
        True se sucesso
    """
    try:
        response = requests.post(
            f"{API_URL}/auth/jwt/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return False


# ============================================================================
# Streamlit UI Functions
# ============================================================================

def render_login_page():
    """
    Renderizar página de login/registro

    Exibe tabs para login e registro
    Gerencia session state para autenticação
    """
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            color: #667eea;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    st.markdown('<h1 class="login-header">🔐 Sistema de Escrituras</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Faça login para continuar</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Criar Conta"])

    # ========================================
    # TAB 1: Login
    # ========================================
    with tab1:
        st.markdown("### Entrar")

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="seu@email.com")
            password = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")

            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            with col2:
                if st.form_submit_button("Limpar", use_container_width=True):
                    st.rerun()

            if submit:
                if not email or not password:
                    st.error("⚠️ Preencha todos os campos")
                else:
                    with st.spinner("Autenticando..."):
                        token_data = login_user(email, password)

                        if token_data:
                            # Salvar token no session state
                            st.session_state.auth_token = token_data["access_token"]
                            st.session_state.user_email = email

                            # Obter dados do usuário
                            user_data = get_current_user(st.session_state.auth_token)

                            if user_data:
                                st.session_state.user_data = user_data
                                st.success(f"✅ Login realizado! Bem-vindo, {email}")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao obter dados do usuário")
                        else:
                            st.error("❌ Email ou senha incorretos")

    # ========================================
    # TAB 2: Registro
    # ========================================
    with tab2:
        st.markdown("### Criar Nova Conta")
        st.info("ℹ️ Após criar sua conta, aguarde aprovação do administrador para usar o sistema.")

        with st.form("register_form"):
            email = st.text_input("📧 Email", placeholder="seu@email.com")
            password = st.text_input("🔒 Senha", type="password", placeholder="Mínimo 8 caracteres")
            password2 = st.text_input("🔒 Confirmar Senha", type="password", placeholder="Digite a senha novamente")

            submit = st.form_submit_button("Criar Conta", type="primary", use_container_width=True)

            if submit:
                # Validações
                if not email or not password or not password2:
                    st.error("⚠️ Preencha todos os campos")
                elif password != password2:
                    st.error("❌ As senhas não coincidem")
                elif len(password) < 8:
                    st.error("❌ A senha deve ter pelo menos 8 caracteres")
                elif "@" not in email:
                    st.error("❌ Email inválido")
                else:
                    with st.spinner("Criando conta..."):
                        success, error = register_user(email, password)

                        if success:
                            st.success("✅ Conta criada com sucesso!")
                            st.info("📧 Aguarde a aprovação do administrador. Você receberá uma notificação quando sua conta for aprovada.")
                            st.balloons()
                        else:
                            if "already exists" in str(error).lower():
                                st.error("❌ Este email já está cadastrado")
                            else:
                                st.error(f"❌ Erro ao criar conta: {error}")

    st.markdown('</div>', unsafe_allow_html=True)


def check_auth() -> bool:
    """
    Verificar se usuário está autenticado E aprovado

    Returns:
        True se autenticado e aprovado
        False caso contrário (exibe mensagens apropriadas)
    """
    # Verificar se tem token
    if 'auth_token' not in st.session_state:
        return False

    # Verificar se token ainda é válido
    user_data = get_current_user(st.session_state.auth_token)

    if not user_data:
        # Token inválido/expirado
        if 'auth_token' in st.session_state:
            del st.session_state.auth_token
        if 'user_data' in st.session_state:
            del st.session_state.user_data
        if 'user_email' in st.session_state:
            del st.session_state.user_email
        return False

    # Atualizar dados do usuário
    st.session_state.user_data = user_data

    # Verificar se usuário está ativo
    if not user_data.get("is_active", False):
        st.error("❌ Sua conta foi desativada. Entre em contato com o administrador.")
        return False

    # Verificar se usuário está aprovado
    if not user_data.get("is_approved", False):
        st.warning("⏳ Sua conta ainda não foi aprovada pelo administrador.")
        st.info("📧 Entre em contato com o suporte para liberar seu acesso.")
        st.info(f"**Sua conta:** {user_data.get('email')}")

        # Botão de logout
        if st.button("🚪 Sair"):
            logout_user(st.session_state.auth_token)
            del st.session_state.auth_token
            del st.session_state.user_data
            del st.session_state.user_email
            st.rerun()

        return False

    # Usuário autenticado e aprovado! ✅
    return True


def render_user_info_sidebar():
    """
    Renderizar informações do usuário na sidebar

    Exibe email, status de aprovação, botão de logout
    """
    if 'user_data' in st.session_state:
        user = st.session_state.user_data

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Usuário")
        st.sidebar.markdown(f"**Email:** {user.get('email')}")

        # Badges de status
        if user.get('is_approved'):
            st.sidebar.success("✅ Aprovado")
        else:
            st.sidebar.warning("⏳ Aguardando aprovação")

        if user.get('is_superuser'):
            st.sidebar.info("👑 Administrador")

        st.sidebar.markdown("---")

        # Botão de logout
        if st.sidebar.button("🚪 Sair", use_container_width=True):
            logout_user(st.session_state.auth_token)
            del st.session_state.auth_token
            del st.session_state.user_data
            del st.session_state.user_email
            st.rerun()


# ============================================================================
# Helper Functions
# ============================================================================

def get_auth_headers() -> Dict[str, str]:
    """
    Obter headers de autenticação para requests

    Returns:
        dict com Authorization header se autenticado
        dict vazio caso contrário
    """
    if 'auth_token' in st.session_state:
        return {"Authorization": f"Bearer {st.session_state.auth_token}"}
    return {}


def is_admin() -> bool:
    """
    Verificar se usuário atual é admin

    Returns:
        True se é superuser
    """
    if 'user_data' in st.session_state:
        return st.session_state.user_data.get('is_superuser', False)
    return False
