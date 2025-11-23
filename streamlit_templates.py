"""
Streamlit Template Editor Page - Enhanced Version
Interface avançada para gerenciar templates com múltiplos blocos
"""
import streamlit as st
import requests
from typing import Dict, List, Any, Optional
import json
import re


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


def preview_template(template_id: int, dados_exemplo: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Gera preview do template com dados de exemplo"""
    try:
        headers = get_auth_headers()
        headers["Content-Type"] = "application/json"

        response = requests.post(
            f"{API_BASE_URL}/templates/{template_id}/preview",
            headers=headers,
            json={"dados_exemplo": dados_exemplo},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao gerar preview: {error_detail}")
            return None

    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return None


def extract_variables_from_content(content: str) -> List[str]:
    """Extrai variáveis [VARIAVEL] do conteúdo"""
    pattern = r'\[([A-Z_]+)\]'
    matches = re.findall(pattern, content)
    return list(set(matches))


def render_templates_sidebar():
    """Renderiza informações de templates na sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 Templates")

    templates = list_user_templates()

    if templates:
        total = len(templates)
        defaults = sum(1 for t in templates if t.get('is_default', False))

        st.sidebar.metric("Total de Templates", total)
        st.sidebar.metric("Templates Padrão", defaults)

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

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        tipo_filter = st.selectbox(
            "Filtrar por tipo:",
            ["Todos", "lote", "apto", "rural", "rural_desmembramento"],
            key="tipo_filter"
        )

    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("➕ Novo", type="primary", use_container_width=True):
            st.session_state.template_view = "create"
            st.rerun()

    filter_value = None if tipo_filter == "Todos" else tipo_filter
    templates = list_user_templates(filter_value)

    if not templates:
        st.info("📭 Você ainda não possui templates. Crie seu primeiro template!")
        return

    st.markdown("---")

    for template in templates:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                default_icon = "⭐ " if template.get('is_default', False) else ""
                st.markdown(f"**{default_icon}{template.get('nome_template', 'Sem nome')}**")
                st.caption(f"Tipo: {template.get('tipo_escritura', 'N/A')}")

            with col2:
                blocos_count = len(template.get('template_json', {}).get('blocos', []))
                st.metric("Blocos", blocos_count)

            with col3:
                if st.button("👁️", key=f"view_{template['id']}", use_container_width=True, help="Visualizar"):
                    st.session_state.viewing_template_id = template['id']
                    st.rerun()

            with col4:
                if st.button("✏️", key=f"edit_{template['id']}", use_container_width=True, help="Editar"):
                    st.session_state.editing_template_id = template['id']
                    st.session_state.template_view = "edit"
                    st.rerun()

            with col5:
                if st.button("🗑️", key=f"del_{template['id']}", use_container_width=True, help="Deletar"):
                    if delete_template(template['id']):
                        st.rerun()

            st.markdown("---")


def render_block_editor(blocos: List[Dict], block_index: int):
    """Renderiza editor para um bloco específico"""
    bloco = blocos[block_index] if block_index < len(blocos) else None

    if not bloco:
        st.warning("Bloco não encontrado")
        return blocos

    st.markdown(f"#### 📦 Bloco {bloco.get('ordem', block_index + 1)}")

    col1, col2 = st.columns([2, 1])

    with col1:
        tipo = st.text_input(
            "Tipo do Bloco",
            value=bloco.get('tipo', ''),
            key=f"tipo_{block_index}",
            help="Ex: cabecalho, partes, descricao_imovel"
        )

    with col2:
        ordem = st.number_input(
            "Ordem",
            min_value=1,
            value=bloco.get('ordem', block_index + 1),
            key=f"ordem_{block_index}"
        )

    conteudo = st.text_area(
        "Conteúdo",
        value=bloco.get('conteudo', ''),
        height=200,
        key=f"conteudo_{block_index}",
        help="Use [VARIAVEL] para placeholders dinâmicos"
    )

    # Formatação
    with st.expander("⚙️ Formatação"):
        formatacao = bloco.get('formatacao', {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            negrito = st.checkbox("Negrito", value=formatacao.get('negrito', False), key=f"negrito_{block_index}")

        with col2:
            italico = st.checkbox("Itálico", value=formatacao.get('italico', False), key=f"italico_{block_index}")

        with col3:
            sublinhado = st.checkbox("Sublinhado", value=formatacao.get('sublinhado', False), key=f"sublinhado_{block_index}")

        with col4:
            alinhamento = st.selectbox(
                "Alinhamento",
                ["left", "center", "right", "justify"],
                index=["left", "center", "right", "justify"].index(formatacao.get('alinhamento', 'justify')),
                key=f"align_{block_index}"
            )

    # Atualizar bloco
    blocos[block_index] = {
        "id": bloco.get('id', f"bloco_{block_index + 1}"),
        "tipo": tipo,
        "ordem": ordem,
        "conteudo": conteudo,
        "formatacao": {
            "negrito": negrito,
            "italico": italico,
            "sublinhado": sublinhado,
            "alinhamento": alinhamento
        }
    }

    return blocos


def render_advanced_template_editor(template_id: Optional[int] = None):
    """Renderiza editor avançado de template com múltiplos blocos"""
    st.markdown("### ✏️ Editor Avançado de Template")

    # Buscar template se editando
    existing_template = None
    if template_id:
        existing_template = get_template_by_id(template_id)
        if not existing_template:
            st.error("❌ Template não encontrado!")
            return

    # Inicializar estado dos blocos
    if 'editing_blocos' not in st.session_state or st.session_state.get('current_template_id') != template_id:
        if existing_template:
            st.session_state.editing_blocos = existing_template.get('template_json', {}).get('blocos', [])
        else:
            st.session_state.editing_blocos = [{
                "id": "bloco_1",
                "tipo": "conteudo",
                "ordem": 1,
                "conteudo": "",
                "formatacao": {"negrito": False, "italico": False, "sublinhado": False, "alinhamento": "justify"}
            }]
        st.session_state.current_template_id = template_id

    # Metadados do template
    with st.form("template_metadata"):
        col1, col2 = st.columns([2, 1])

        with col1:
            nome_template = st.text_input(
                "Nome do Template *",
                value=existing_template.get('nome_template', '') if existing_template else '',
                placeholder="Ex: Meu Template Personalizado"
            )

        with col2:
            tipo_escritura = st.selectbox(
                "Tipo *",
                ["lote", "apto", "rural", "rural_desmembramento"],
                index=["lote", "apto", "rural", "rural_desmembramento"].index(existing_template['tipo_escritura']) if existing_template else 0,
                disabled=bool(existing_template)
            )

        is_default = st.checkbox(
            "✨ Template padrão para este tipo",
            value=existing_template.get('is_default', False) if existing_template else False
        )

        if st.form_submit_button("💾 Salvar Metadados"):
            st.success("Metadados atualizados temporariamente. Salve o template para confirmar.")

    st.markdown("---")
    st.markdown("### 📦 Blocos do Template")

    # Gerenciamento de blocos
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**Total de blocos: {len(st.session_state.editing_blocos)}**")

    with col2:
        if st.button("➕ Adicionar Bloco", use_container_width=True):
            new_bloco = {
                "id": f"bloco_{len(st.session_state.editing_blocos) + 1}",
                "tipo": "novo_bloco",
                "ordem": len(st.session_state.editing_blocos) + 1,
                "conteudo": "",
                "formatacao": {"negrito": False, "italico": False, "sublinhado": False, "alinhamento": "justify"}
            }
            st.session_state.editing_blocos.append(new_bloco)
            st.rerun()

    with col3:
        if len(st.session_state.editing_blocos) > 1:
            if st.button("🗑️ Remover Último", use_container_width=True):
                st.session_state.editing_blocos.pop()
                st.rerun()

    # Editor de blocos em tabs
    if st.session_state.editing_blocos:
        tab_labels = [f"Bloco {i+1}" for i in range(len(st.session_state.editing_blocos))]
        tabs = st.tabs(tab_labels)

        for idx, tab in enumerate(tabs):
            with tab:
                st.session_state.editing_blocos = render_block_editor(st.session_state.editing_blocos, idx)

    st.markdown("---")

    # Botões finais
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Salvar Template", type="primary", use_container_width=True):
            # Extrair todas as variáveis
            all_content = " ".join([b.get('conteudo', '') for b in st.session_state.editing_blocos])
            variaveis = extract_variables_from_content(all_content)

            template_data = {
                "tipo_escritura": tipo_escritura,
                "nome_template": nome_template,
                "is_default": is_default,
                "template_json": {
                    "blocos": st.session_state.editing_blocos,
                    "variaveis_usadas": variaveis
                },
                "configuracoes_json": {
                    "terminologia": {"vendedor": "VENDEDOR", "comprador": "COMPRADOR", "imovel": "IMÓVEL"},
                    "formatacao": {"titulos_negrito": True, "variaveis_destacadas": True},
                    "layout": {"fonte": "Times New Roman", "tamanho_fonte_padrao": 12}
                }
            }

            if existing_template:
                if update_template(template_id, template_data):
                    del st.session_state.editing_blocos
                    del st.session_state.current_template_id
                    st.session_state.template_view = "list"
                    st.rerun()
            else:
                if create_template(template_data):
                    del st.session_state.editing_blocos
                    st.session_state.template_view = "list"
                    st.rerun()

    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            if 'editing_blocos' in st.session_state:
                del st.session_state.editing_blocos
            if 'current_template_id' in st.session_state:
                del st.session_state.current_template_id
            st.session_state.template_view = "list"
            st.rerun()


def render_template_viewer(template_id: int):
    """Renderiza visualização de um template"""
    template = get_template_by_id(template_id)

    if not template:
        st.error("Template não encontrado")
        return

    st.markdown(f"### 👁️ Visualização: {template.get('nome_template', 'Sem nome')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tipo", template.get('tipo_escritura', 'N/A'))
    with col2:
        blocos_count = len(template.get('template_json', {}).get('blocos', []))
        st.metric("Blocos", blocos_count)
    with col3:
        vars_count = len(template.get('template_json', {}).get('variaveis_usadas', []))
        st.metric("Variáveis", vars_count)

    st.markdown("---")

    # Mostrar blocos
    blocos = sorted(
        template.get('template_json', {}).get('blocos', []),
        key=lambda b: b.get('ordem', 0)
    )

    for bloco in blocos:
        with st.expander(f"📦 Bloco {bloco.get('ordem', '?')}: {bloco.get('tipo', 'sem tipo')}", expanded=True):
            st.text(bloco.get('conteudo', ''))

            formatacao = bloco.get('formatacao', {})
            if any([formatacao.get('negrito'), formatacao.get('italico'), formatacao.get('sublinhado')]):
                fmt_str = []
                if formatacao.get('negrito'):
                    fmt_str.append("**Negrito**")
                if formatacao.get('italico'):
                    fmt_str.append("*Itálico*")
                if formatacao.get('sublinhado'):
                    fmt_str.append("__Sublinhado__")

                st.caption(f"Formatação: {', '.join(fmt_str)} | Alinhamento: {formatacao.get('alinhamento', 'justify')}")

    st.markdown("---")

    if st.button("⬅️ Voltar para lista"):
        if 'viewing_template_id' in st.session_state:
            del st.session_state.viewing_template_id
        st.rerun()


def render_template_editor_page():
    """Renderiza página principal de edição de templates"""

    if 'template_view' not in st.session_state:
        st.session_state.template_view = "list"

    st.markdown('<div class="main-header">📝 Editor de Templates</div>', unsafe_allow_html=True)
    st.markdown("### Gerencie seus templates de escrituras")

    if 'access_token' not in st.session_state or not st.session_state.access_token:
        st.warning("⚠️ Você precisa estar autenticado para gerenciar templates.")
        st.info("Faça login na página principal do sistema.")
        return

    render_templates_sidebar()

    st.markdown("---")

    # Renderizar visualização apropriada
    if 'viewing_template_id' in st.session_state:
        render_template_viewer(st.session_state.viewing_template_id)

    elif st.session_state.template_view == "list":
        render_template_list_view()

    elif st.session_state.template_view in ["edit", "create"]:
        template_id = st.session_state.get('editing_template_id') if st.session_state.template_view == "edit" else None
        render_advanced_template_editor(template_id)
