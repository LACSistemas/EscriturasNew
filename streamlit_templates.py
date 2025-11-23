"""
Streamlit Template Editor Page
Interface para gerenciar templates de escrituras
"""
import streamlit as st
import requests
from typing import Dict, List, Any, Optional
import json


# Configurações da API
API_BASE_URL = "http://localhost:8000"


def get_auth_headers() -> Dict[str, str]:
    """Retorna headers com token de autenticação"""
    if 'access_token' not in st.session_state or not st.session_state.access_token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def list_user_templates(tipo_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista templates do usuário"""
    try:
        headers = get_auth_headers()
        params = {"tipo": tipo_filter} if tipo_filter else {}

        response = requests.get(
            f"{API_BASE_URL}/templates",
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return data.get('templates', [])
        elif response.status_code == 401:
            st.error("❌ Não autenticado. Faça login novamente.")
            return []
        else:
            st.error(f"❌ Erro ao listar templates: {response.status_code}")
            return []

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return []


def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
    """Busca template por ID"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{API_BASE_URL}/templates/{template_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Erro ao buscar template: {response.status_code}")
            return None

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return None


def create_template(template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Cria novo template"""
    try:
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        response = requests.post(
            f"{API_BASE_URL}/templates",
            headers=headers,
            json=template_data,
            timeout=10
        )

        if response.status_code == 201:
            result = response.json()
            st.success(f"✅ {result.get('message', 'Template criado com sucesso!')}")
            return result.get('template')
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao criar template: {error_detail}")
            return None

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return None


def update_template(template_id: int, template_data: Dict[str, Any]) -> bool:
    """Atualiza template existente"""
    try:
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        response = requests.put(
            f"{API_BASE_URL}/templates/{template_id}",
            headers=headers,
            json=template_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ {result.get('message', 'Template atualizado com sucesso!')}")
            return True
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao atualizar template: {error_detail}")
            return False

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return False


def delete_template(template_id: int) -> bool:
    """Deleta template (soft delete)"""
    try:
        headers = get_auth_headers()

        response = requests.delete(
            f"{API_BASE_URL}/templates/{template_id}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ {result.get('message', 'Template deletado com sucesso!')}")
            return True
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao deletar template: {error_detail}")
            return False

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return False


def duplicate_template(template_id: int, new_name: str) -> Optional[Dict[str, Any]]:
    """Duplica um template existente"""
    try:
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        response = requests.post(
            f"{API_BASE_URL}/templates/{template_id}/duplicate",
            headers=headers,
            json={"novo_nome": new_name},
            timeout=10
        )

        if response.status_code == 201:
            result = response.json()
            st.success(f"✅ {result.get('message', 'Template duplicado com sucesso!')}")
            return result.get('template')
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao duplicar template: {error_detail}")
            return None

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return None


def render_templates_sidebar():
    """Renderiza informações de templates na sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 Templates")

    # Contadores rápidos
    templates = list_user_templates()

    if templates:
        total = len(templates)
        defaults = sum(1 for t in templates if t.get('is_default', False))

        st.sidebar.metric("Total de Templates", total)
        st.sidebar.metric("Templates Padrão", defaults)

        # Por tipo
        tipos = {}
        for t in templates:
            tipo = t.get('tipo_escritura', 'unknown')
            tipos[tipo] = tipos.get(tipo, 0) + 1

        st.sidebar.markdown("**Por Tipo:**")
        for tipo, count in sorted(tipos.items()):
            st.sidebar.text(f"  • {tipo}: {count}")
    else:
        st.sidebar.info("Nenhum template encontrado")


def render_template_list_view():
    """Renderiza visualização de lista de templates"""
    st.markdown("### 📋 Meus Templates")

    # Filtros
    col1, col2 = st.columns([3, 1])

    with col1:
        tipo_filter = st.selectbox(
            "Filtrar por tipo:",
            ["Todos", "lote", "apto", "rural", "rural_desmembramento"],
            key="tipo_filter"
        )

    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    # Buscar templates
    filter_value = None if tipo_filter == "Todos" else tipo_filter
    templates = list_user_templates(filter_value)

    if not templates:
        st.info("📭 Você ainda não possui templates. Crie seu primeiro template abaixo!")
        return

    # Exibir templates em cards
    st.markdown("---")

    for template in templates:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

            with col1:
                default_icon = "⭐ " if template.get('is_default', False) else ""
                st.markdown(f"**{default_icon}{template.get('nome_template', 'Sem nome')}**")
                st.caption(f"Tipo: {template.get('tipo_escritura', 'N/A')}")

            with col2:
                blocos_count = len(template.get('template_json', {}).get('blocos', []))
                vars_count = len(template.get('template_json', {}).get('variaveis_usadas', []))
                st.text(f"📦 {blocos_count} blocos")
                st.text(f"🔤 {vars_count} variáveis")

            with col3:
                if st.button("✏️ Editar", key=f"edit_{template['id']}", use_container_width=True):
                    st.session_state.editing_template_id = template['id']
                    st.session_state.template_view = "edit"
                    st.rerun()

            with col4:
                if st.button("📋 Duplicar", key=f"dup_{template['id']}", use_container_width=True):
                    st.session_state.duplicating_template_id = template['id']
                    st.rerun()

            st.markdown("---")


def render_template_editor(template_id: Optional[int] = None):
    """Renderiza editor de template"""
    st.markdown("### ✏️ Editor de Template")

    # Buscar template se editando
    existing_template = None
    if template_id:
        existing_template = get_template_by_id(template_id)
        if not existing_template:
            st.error("❌ Template não encontrado!")
            return

    # Formulário
    with st.form("template_form"):
        # Tipo de escritura
        tipo_escritura = st.selectbox(
            "Tipo de Escritura *",
            ["lote", "apto", "rural", "rural_desmembramento"],
            index=["lote", "apto", "rural", "rural_desmembramento"].index(existing_template['tipo_escritura']) if existing_template else 0,
            disabled=bool(existing_template)  # Não permite alterar tipo ao editar
        )

        # Nome do template
        nome_template = st.text_input(
            "Nome do Template *",
            value=existing_template.get('nome_template', '') if existing_template else '',
            placeholder="Ex: Meu Template Personalizado"
        )

        # Template padrão
        is_default = st.checkbox(
            "Definir como template padrão para este tipo",
            value=existing_template.get('is_default', False) if existing_template else False
        )

        st.markdown("---")
        st.markdown("#### 📝 Conteúdo do Template")

        # Área de texto para edição simplificada
        current_content = ""
        if existing_template:
            # Concatenar blocos ordenados
            blocos = sorted(
                existing_template.get('template_json', {}).get('blocos', []),
                key=lambda b: b.get('ordem', 0)
            )
            current_content = "\n\n".join([
                f"### BLOCO {b.get('ordem', '?')}: {b.get('tipo', 'sem tipo')}\n{b.get('conteudo', '')}"
                for b in blocos
            ])

        template_content = st.text_area(
            "Conteúdo (use [VARIAVEL] para variáveis dinâmicas)",
            value=current_content,
            height=400,
            help="Digite o conteúdo do template. Use [VARIAVEL_NOME] para variáveis que serão substituídas."
        )

        st.markdown("---")

        # Botões
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            submit = st.form_submit_button(
                "💾 Salvar Template",
                type="primary",
                use_container_width=True
            )

        with col2:
            cancel = st.form_submit_button(
                "❌ Cancelar",
                use_container_width=True
            )

        if submit:
            if not nome_template:
                st.error("❌ Nome do template é obrigatório!")
                return

            # Preparar dados (formato simplificado por enquanto)
            template_data = {
                "tipo_escritura": tipo_escritura,
                "nome_template": nome_template,
                "is_default": is_default,
                "template_json": {
                    "blocos": [
                        {
                            "id": "bloco_1",
                            "tipo": "conteudo_geral",
                            "ordem": 1,
                            "conteudo": template_content,
                            "formatacao": {
                                "negrito": False,
                                "italico": False,
                                "sublinhado": False,
                                "alinhamento": "justify"
                            }
                        }
                    ],
                    "variaveis_usadas": extract_variables_from_content(template_content)
                },
                "configuracoes_json": {
                    "terminologia": {
                        "vendedor": "VENDEDOR",
                        "comprador": "COMPRADOR",
                        "imovel": "IMÓVEL"
                    },
                    "formatacao": {
                        "titulos_negrito": True,
                        "variaveis_destacadas": True,
                        "numeracao_automatica": True
                    },
                    "layout": {
                        "margem_superior": 2.5,
                        "margem_inferior": 2.5,
                        "margem_esquerda": 3.0,
                        "margem_direita": 3.0,
                        "espacamento_entre_linhas": 1.5,
                        "fonte": "Times New Roman",
                        "tamanho_fonte_padrao": 12
                    }
                }
            }

            # Criar ou atualizar
            if existing_template:
                success = update_template(template_id, template_data)
                if success:
                    st.session_state.template_view = "list"
                    st.rerun()
            else:
                new_template = create_template(template_data)
                if new_template:
                    st.session_state.template_view = "list"
                    st.rerun()

        if cancel:
            st.session_state.template_view = "list"
            if 'editing_template_id' in st.session_state:
                del st.session_state.editing_template_id
            st.rerun()


def extract_variables_from_content(content: str) -> List[str]:
    """Extrai variáveis [VARIAVEL] do conteúdo"""
    import re
    pattern = r'\[([A-Z_]+)\]'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Remove duplicatas


def render_template_editor_page():
    """Renderiza página principal de edição de templates"""

    # Inicializar estado
    if 'template_view' not in st.session_state:
        st.session_state.template_view = "list"

    # Header
    st.markdown('<div class="main-header">📝 Editor de Templates</div>', unsafe_allow_html=True)
    st.markdown("### Gerencie seus templates de escrituras")

    # Verificar autenticação
    if 'access_token' not in st.session_state or not st.session_state.access_token:
        st.warning("⚠️ Você precisa estar autenticado para gerenciar templates.")
        st.info("Faça login na página principal do sistema.")
        return

    # Renderizar sidebar info
    render_templates_sidebar()

    # Botão novo template (sempre visível)
    if st.session_state.template_view == "list":
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("➕ Novo Template", type="primary", use_container_width=True):
                st.session_state.template_view = "create"
                st.rerun()

    st.markdown("---")

    # Renderizar visualização apropriada
    if st.session_state.template_view == "list":
        render_template_list_view()

    elif st.session_state.template_view == "edit":
        template_id = st.session_state.get('editing_template_id')
        render_template_editor(template_id)

    elif st.session_state.template_view == "create":
        render_template_editor()

    # Handle duplicação
    if 'duplicating_template_id' in st.session_state:
        template_id = st.session_state.duplicating_template_id

        with st.form("duplicate_form"):
            st.markdown("### 📋 Duplicar Template")
            new_name = st.text_input("Nome do novo template:")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Duplicar", use_container_width=True):
                    if new_name:
                        result = duplicate_template(template_id, new_name)
                        if result:
                            del st.session_state.duplicating_template_id
                            st.rerun()
                    else:
                        st.error("Nome é obrigatório!")

            with col2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    del st.session_state.duplicating_template_id
                    st.rerun()
