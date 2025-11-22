"""
Interface Streamlit para configuração de cartório
Permite que usuários configurem os dados do cartório diretamente no app
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any
from streamlit_login import get_auth_headers

# URL da API (configurável via environment ou hardcoded para dev)
API_URL = "http://localhost:8000"


def get_cartorio_config() -> Optional[Dict[str, Any]]:
    """Busca configuração de cartório do usuário atual"""
    try:
        response = requests.get(
            f"{API_URL}/cartorio/config",
            headers=get_auth_headers()
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # Configuração não existe ainda
        else:
            st.error(f"Erro ao buscar configuração: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None


def create_cartorio_config(config_data: Dict[str, Any]) -> bool:
    """Cria nova configuração de cartório"""
    try:
        response = requests.post(
            f"{API_URL}/cartorio/config",
            json=config_data,
            headers=get_auth_headers()
        )

        if response.status_code == 201:
            result = response.json()
            st.success(result.get("message", "Configuração criada com sucesso!"))
            return True
        elif response.status_code == 409:
            st.warning("Configuração já existe. Use a opção de atualizar.")
            return False
        else:
            st.error(f"Erro ao criar configuração: {response.json().get('detail', 'Erro desconhecido')}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {str(e)}")
        return False


def update_cartorio_config(config_data: Dict[str, Any]) -> bool:
    """Atualiza configuração de cartório existente"""
    try:
        response = requests.put(
            f"{API_URL}/cartorio/config",
            json=config_data,
            headers=get_auth_headers()
        )

        if response.status_code == 200:
            result = response.json()
            st.success(result.get("message", "Configuração atualizada com sucesso!"))
            return True
        elif response.status_code == 404:
            st.warning("Configuração não encontrada. Use a opção de criar.")
            return False
        else:
            st.error(f"Erro ao atualizar configuração: {response.json().get('detail', 'Erro desconhecido')}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {str(e)}")
        return False


def check_config_completeness() -> Dict[str, Any]:
    """Verifica se configuração está completa"""
    try:
        response = requests.get(
            f"{API_URL}/cartorio/config/check",
            headers=get_auth_headers()
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"exists": False, "is_complete": False, "missing_fields": []}

    except requests.exceptions.RequestException:
        return {"exists": False, "is_complete": False, "missing_fields": []}


def render_cartorio_config_page():
    """
    Renderiza a página de configuração de cartório
    Pode ser chamada como uma página separada ou como parte da sidebar
    """
    st.header("⚙️ Configuração do Cartório")

    st.markdown("""
    Configure aqui os dados do cartório que serão utilizados na geração das escrituras.
    Todos os campos são importantes para garantir documentos completos e corretos.
    """)

    # Buscar configuração existente
    existing_config = get_cartorio_config()

    # Verificar completude
    completeness = check_config_completeness()

    if completeness.get("exists") and not completeness.get("is_complete"):
        st.warning(f"⚠️ Configuração incompleta! Campos faltando: {', '.join(completeness.get('missing_fields', []))}")
    elif completeness.get("is_complete"):
        st.success("✅ Configuração completa!")

    # Formulário de configuração
    with st.form("cartorio_config_form"):
        st.subheader("Dados do Cartório")

        nome_cartorio = st.text_input(
            "Nome do Cartório *",
            value=existing_config.get("nome_cartorio", "") if existing_config else "",
            placeholder="Ex: 1º Tabelionato de Notas de São Paulo",
            help="Nome completo do cartório"
        )

        endereco_cartorio = st.text_input(
            "Endereço do Cartório *",
            value=existing_config.get("endereco_cartorio", "") if existing_config else "",
            placeholder="Ex: Rua da República, 123 - Centro",
            help="Endereço completo do cartório"
        )

        col1, col2 = st.columns(2)
        with col1:
            cidade_cartorio = st.text_input(
                "Cidade *",
                value=existing_config.get("cidade_cartorio", "") if existing_config else "",
                placeholder="Ex: São Paulo",
                help="Cidade onde o cartório está localizado"
            )

        with col2:
            estado_cartorio = st.text_input(
                "Estado (UF) *",
                value=existing_config.get("estado_cartorio", "") if existing_config else "",
                placeholder="Ex: SP",
                help="Estado (UF) - 2 letras",
                max_chars=2
            )

        quem_assina = st.text_input(
            "Quem Assina *",
            value=existing_config.get("quem_assina", "") if existing_config else "",
            placeholder="Ex: Dr. João da Silva - Tabelião",
            help="Nome de quem assina pelo cartório"
        )

        st.markdown("---")

        # Botões de ação
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            submit_button = st.form_submit_button(
                "💾 Salvar",
                use_container_width=True,
                type="primary"
            )

        with col2:
            clear_button = st.form_submit_button(
                "🗑️ Limpar",
                use_container_width=True
            )

        # Processar envio do formulário
        if submit_button:
            # Validar campos obrigatórios
            if not all([nome_cartorio, endereco_cartorio, cidade_cartorio, estado_cartorio, quem_assina]):
                st.error("❌ Por favor, preencha todos os campos obrigatórios!")
            elif len(estado_cartorio) != 2:
                st.error("❌ Estado deve ter exatamente 2 letras (ex: SP, RJ, MG)")
            else:
                config_data = {
                    "nome_cartorio": nome_cartorio.strip(),
                    "endereco_cartorio": endereco_cartorio.strip(),
                    "cidade_cartorio": cidade_cartorio.strip(),
                    "estado_cartorio": estado_cartorio.strip().upper(),
                    "quem_assina": quem_assina.strip()
                }

                # Criar ou atualizar dependendo se já existe
                if existing_config:
                    success = update_cartorio_config(config_data)
                else:
                    success = create_cartorio_config(config_data)

                if success:
                    st.rerun()  # Recarregar página para mostrar dados atualizados

        if clear_button:
            st.info("Use os campos acima para preencher a configuração")


def render_cartorio_config_sidebar():
    """
    Renderiza status da configuração de cartório na sidebar
    Mostra se está completa ou não, com link para configurar
    """
    completeness = check_config_completeness()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Cartório")

    if not completeness.get("exists"):
        st.sidebar.warning("⚠️ Não configurado")
        st.sidebar.caption("Configure os dados do cartório para começar")
    elif not completeness.get("is_complete"):
        st.sidebar.warning("⚠️ Incompleto")
        missing = completeness.get("missing_fields", [])
        st.sidebar.caption(f"Faltam: {len(missing)} campos")
    else:
        st.sidebar.success("✅ Configurado")

    # Botão para ir para página de configuração
    # (Este botão pode ser usado para navegar para a página de config)
    # st.sidebar.button("⚙️ Configurar Cartório", key="config_cartorio_btn")


def get_cartorio_info_text() -> str:
    """
    Retorna texto formatado com informações do cartório
    Útil para mostrar em rodapés de documentos, etc.
    """
    config = get_cartorio_config()

    if not config:
        return "Cartório não configurado"

    return f"""
{config.get('nome_cartorio', 'N/A')}
{config.get('endereco_cartorio', 'N/A')}
{config.get('cidade_cartorio', 'N/A')} - {config.get('estado_cartorio', 'N/A')}

Assinatura: {config.get('quem_assina', 'N/A')}
    """.strip()


# Estados brasileiros válidos (para validação no frontend se necessário)
ESTADOS_BR = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]
