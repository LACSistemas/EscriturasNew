"""
Streamlit Interface para Sistema de Escrituras
Interface interativa para testar o fluxo completo da State Machine
"""

import streamlit as st
import asyncio
import sys
from typing import Dict, Any, List
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, '/home/user/EscriturasNew')

# Load environment variables
load_dotenv()

from workflow.flow_definition import create_workflow
from workflow.state_machine import WorkflowStateMachine, StepType
from models.session import create_new_session_dict

# Import dummy data generators for testing
from tests.test_dummy_data import (
    generate_rg_data, generate_cnh_data, generate_ctps_data,
    generate_empresa_data, generate_certidao_casamento_data,
    generate_certidao_nascimento_data, generate_certidao_negativa_data,
    generate_certidao_matricula_data, generate_certidao_iptu_data,
    generate_certidao_onus_data, generate_certidao_condominio_data,
    generate_certidao_objeto_pe_data, generate_certidao_itr_data,
    generate_certidao_ccir_data, generate_certidao_incra_data,
    generate_certidao_ibama_data, generate_art_desmembramento_data,
    generate_planta_desmembramento_data, MockOCRService, MockAIService
)

# Page config
st.set_page_config(
    page_title="Sistema de Escrituras",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .step-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'workflow' not in st.session_state:
        st.session_state.workflow = create_workflow()

    if 'session_data' not in st.session_state:
        session_id = f"streamlit-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        st.session_state.session_data = create_new_session_dict(session_id)
        st.session_state.session_data["current_step"] = st.session_state.workflow.initial_step

    if 'history' not in st.session_state:
        st.session_state.history = []

    if 'use_dummy_data' not in st.session_state:
        st.session_state.use_dummy_data = True

    if 'mock_ocr' not in st.session_state:
        st.session_state.mock_ocr = MockOCRService()
        st.session_state.mock_ai = MockAIService()
        
    # Initialize real API clients if not using dummy data
    if 'vision_client' not in st.session_state:
        st.session_state.vision_client = None
        st.session_state.gemini_model = None
        
    if not st.session_state.use_dummy_data and st.session_state.vision_client is None:
        init_real_apis()

def init_real_apis():
    """Initialize real Google Cloud APIs"""
    try:
        from google.cloud import vision
        import google.generativeai as genai
        
        # Configure Google Cloud credentials
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            st.session_state.vision_client = vision.ImageAnnotatorClient()
        
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        if api_key:
            genai.configure(api_key=api_key)
            st.session_state.gemini_model = genai.GenerativeModel(model_name)
            
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao inicializar APIs: {e}")
        return False

def reset_session():
    """Reset the session"""
    session_id = f"streamlit-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    st.session_state.session_data = create_new_session_dict(session_id)
    st.session_state.session_data["current_step"] = st.session_state.workflow.initial_step
    st.session_state.history = []
    st.rerun()

def add_to_history(action: str, details: str):
    """Add action to history"""
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "details": details
    })

def get_dummy_data_for_step(step_name: str) -> bytes:
    """Get dummy data based on step name"""
    # Map step names to generators
    generators = {
        "rg": lambda: generate_rg_data("Masculino"),
        "cnh": lambda: generate_cnh_data("Masculino"),
        "ctps": lambda: generate_ctps_data("Masculino"),
        "empresa": generate_empresa_data,
        "casamento": generate_certidao_casamento_data,
        "nascimento": generate_certidao_nascimento_data,
        "negativa": generate_certidao_negativa_data,
        "matricula": generate_certidao_matricula_data,
        "iptu": generate_certidao_iptu_data,
        "onus": generate_certidao_onus_data,
        "condominio": generate_certidao_condominio_data,
        "objeto": generate_certidao_objeto_pe_data,
        "itr": generate_certidao_itr_data,
        "ccir": generate_certidao_ccir_data,
        "incra": generate_certidao_incra_data,
        "ibama": generate_certidao_ibama_data,
        "art": generate_art_desmembramento_data,
        "planta": generate_planta_desmembramento_data,
    }

    # Find matching generator
    for key, generator in generators.items():
        if key in step_name.lower():
            return generator()

    return {}

async def process_step(response=None, file_data=None, filename=None):
    """Process current step"""
    try:
        if st.session_state.use_dummy_data and file_data is not None:
            # Use mock services for dummy data
            from unittest.mock import patch

            current_step = st.session_state.session_data["current_step"]
            dummy_data = get_dummy_data_for_step(current_step)

            def create_mock_ai(data):
                async def mock_extract(*args, **kwargs):
                    return data
                return mock_extract

            with patch('services.ocr_service_async.extract_text_from_file_async',
                      new=st.session_state.mock_ocr.extract_text_from_file_async):
                with patch('workflow.handlers.document_processors.extract_text_from_file_async',
                          new=st.session_state.mock_ocr.extract_text_from_file_async):
                    with patch('services.ai_service_async.extract_data_with_gemini_async',
                              new=create_mock_ai(dummy_data)):
                        with patch('workflow.handlers.document_processors.extract_data_with_gemini_async',
                                  new=create_mock_ai(dummy_data)):
                            await st.session_state.workflow.process_step(
                                session=st.session_state.session_data,
                                response=response,
                                file_data=file_data,
                                filename=filename,
                                vision_client=None,
                                gemini_model=None
                            )
        else:
            # Use real APIs if available
            await st.session_state.workflow.process_step(
                session=st.session_state.session_data,
                response=response,
                file_data=file_data,
                filename=filename,
                vision_client=st.session_state.vision_client,
                gemini_model=st.session_state.gemini_model
            )

        return True, None
    except Exception as e:
        return False, str(e)

def render_sidebar():
    """Render sidebar with session info"""
    st.sidebar.title("📊 Estado da Sessão")

    # Session ID
    st.sidebar.info(f"**ID:** {st.session_state.session_data.get('session_id', 'N/A')}")

    # Current step
    current_step = st.session_state.session_data.get("current_step", "N/A")
    st.sidebar.success(f"**Step Atual:** `{current_step}`")

    # Progress
    total_steps = len(st.session_state.history)
    st.sidebar.metric("Total de Steps", total_steps)

    # Dummy data toggle
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configurações")
    
    # Check if real APIs are configured
    vision_configured = (os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and 
                        os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')))
    gemini_configured = bool(os.getenv('GEMINI_API_KEY'))
    
    if vision_configured and gemini_configured:
        st.sidebar.success("✅ APIs configuradas")
    else:
        st.sidebar.warning("⚠️ APIs não configuradas")
        if not vision_configured:
            st.sidebar.text("- Vision API não configurada")
        if not gemini_configured:
            st.sidebar.text("- Gemini API não configurada")
    
    old_dummy_value = st.session_state.use_dummy_data
    st.session_state.use_dummy_data = st.sidebar.checkbox(
        "Usar Dados Dummy",
        value=st.session_state.use_dummy_data,
        help="Gera automaticamente dados de teste para uploads"
    )
    
    # Initialize APIs when switching from dummy to real
    if old_dummy_value and not st.session_state.use_dummy_data:
        if vision_configured and gemini_configured:
            init_real_apis()
        else:
            st.sidebar.error("Configure as APIs primeiro!")

    # Reset button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Resetar Sessão", type="primary"):
        reset_session()

    # Stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Estatísticas")
    compradores = st.session_state.session_data.get("compradores", [])
    vendedores = st.session_state.session_data.get("vendedores", [])
    certidoes = st.session_state.session_data.get("certidoes", [])

    col1, col2 = st.sidebar.columns(2)
    col1.metric("Compradores", len(compradores))
    col2.metric("Vendedores", len(vendedores))
    st.sidebar.metric("Certidões", len(certidoes))

def render_current_step():
    """Render the current step interface"""
    current_step_name = st.session_state.session_data.get("current_step")

    if current_step_name == "processing":
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("✅ Escritura concluída! Todos os dados foram coletados.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Show final data
        st.markdown("### 📄 Dados Finais")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💰 Informações Financeiras")
            st.write(f"**Valor:** {st.session_state.session_data.get('valor', 'N/A')}")
            st.write(f"**Forma:** {st.session_state.session_data.get('forma_pagamento', 'N/A')}")
            st.write(f"**Meio:** {st.session_state.session_data.get('meio_pagamento', 'N/A')}")

        with col2:
            st.markdown("#### 📝 Tipo")
            st.write(f"**Escritura:** {st.session_state.session_data.get('tipo_escritura', 'N/A')}")

        return

    # Get current step definition
    step_def = st.session_state.workflow.steps.get(current_step_name)

    if not step_def:
        st.error(f"❌ Step '{current_step_name}' não encontrado!")
        return

    # Render step based on type
    st.markdown(f'<div class="step-box">', unsafe_allow_html=True)
    st.markdown(f"### 📍 Step: `{current_step_name}`")
    st.markdown(f"**Tipo:** {step_def.step_type.value}")

    if step_def.step_type == StepType.QUESTION:
        render_question_step(step_def)
    elif step_def.step_type == StepType.FILE_UPLOAD:
        render_file_upload_step(step_def)
    elif step_def.step_type == StepType.TEXT_INPUT:
        render_text_input_step(step_def)
    else:
        st.warning(f"Tipo de step não suportado: {step_def.step_type}")

    st.markdown('</div>', unsafe_allow_html=True)

def render_question_step(step_def):
    """Render a question step"""
    handler = step_def.handler
    question = handler.question if hasattr(handler, 'question') else "Pergunta não disponível"
    options = handler.options if hasattr(handler, 'options') else []

    st.markdown(f"**Pergunta:** {question}")

    if options:
        # Use radio buttons for options
        selected = st.radio(
            "Selecione uma opção:",
            options,
            key=f"question_{step_def.name}"
        )

        if st.button("➡️ Avançar", key=f"btn_{step_def.name}"):
            success, error = asyncio.run(process_step(response=selected))

            if success:
                add_to_history(f"Question: {step_def.name}", f"Resposta: {selected}")
                st.rerun()
            else:
                st.error(f"❌ Erro: {error}")
    else:
        # Free text input
        response = st.text_input(
            "Sua resposta:",
            key=f"text_{step_def.name}"
        )

        if st.button("➡️ Enviar", key=f"btn_{step_def.name}"):
            if response:
                success, error = asyncio.run(process_step(response=response))

                if success:
                    add_to_history(f"Question: {step_def.name}", f"Resposta: {response}")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {error}")
            else:
                st.warning("⚠️ Por favor, insira uma resposta")

def render_file_upload_step(step_def):
    """Render a file upload step"""
    handler = step_def.handler
    question = handler.question if hasattr(handler, 'question') else "Faça upload do arquivo"
    file_description = handler.file_description if hasattr(handler, 'file_description') else "PDF ou imagem"

    st.markdown(f"**Pergunta:** {question}")
    st.markdown(f"*{file_description}*")

    if st.session_state.use_dummy_data:
        st.info("ℹ️ Modo Dados Dummy ativado - clique em 'Upload Automático' para gerar dados de teste")

        if st.button("📤 Upload Automático (Dados Dummy)", key=f"auto_{step_def.name}"):
            # Generate dummy file
            dummy_file = b"DUMMY_FILE_CONTENT"
            filename = f"{step_def.name}.png"

            success, error = asyncio.run(process_step(
                file_data=dummy_file,
                filename=filename
            ))

            if success:
                add_to_history(f"Upload: {step_def.name}", f"Arquivo: {filename} (dummy)")
                st.rerun()
            else:
                st.error(f"❌ Erro: {error}")
    else:
        # Real file upload
        uploaded_file = st.file_uploader(
            "Escolha um arquivo",
            type=["pdf", "png", "jpg", "jpeg"],
            key=f"upload_{step_def.name}"
        )

        if uploaded_file is not None:
            st.success(f"✅ Arquivo selecionado: {uploaded_file.name}")

            if st.button("📤 Fazer Upload", key=f"btn_{step_def.name}"):
                file_data = uploaded_file.read()

                success, error = asyncio.run(process_step(
                    file_data=file_data,
                    filename=uploaded_file.name
                ))

                if success:
                    add_to_history(f"Upload: {step_def.name}", f"Arquivo: {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {error}")

def render_text_input_step(step_def):
    """Render a text input step"""
    handler = step_def.handler
    question = handler.question if hasattr(handler, 'question') else "Digite sua resposta"
    placeholder = handler.placeholder if hasattr(handler, 'placeholder') else ""

    st.markdown(f"**Pergunta:** {question}")

    # Text input with placeholder
    response = st.text_input(
        "Sua resposta:",
        placeholder=placeholder,
        key=f"textinput_{step_def.name}"
    )

    # Show example if placeholder exists
    if placeholder:
        st.markdown(f"*Exemplo: {placeholder}*")

    if st.button("➡️ Enviar", key=f"btn_{step_def.name}"):
        if response:
            success, error = asyncio.run(process_step(response=response))

            if success:
                add_to_history(f"Text Input: {step_def.name}", f"Resposta: {response}")
                st.rerun()
            else:
                st.error(f"❌ Erro: {error}")
        else:
            st.warning("⚠️ Por favor, insira uma resposta")

def render_data_view():
    """Render collected data view"""
    st.markdown("---")
    st.markdown("## 📊 Dados Coletados")

    tabs = st.tabs(["👥 Compradores", "🏪 Vendedores", "📜 Certidões", "📋 Histórico"])

    # Tab 1: Compradores
    with tabs[0]:
        compradores = st.session_state.session_data.get("compradores", [])
        if compradores:
            for i, comp in enumerate(compradores, 1):
                with st.expander(f"Comprador {i}: {comp.get('nome_completo', 'N/A')}", expanded=True):
                    st.json(comp)
        else:
            st.info("Nenhum comprador cadastrado ainda")

    # Tab 2: Vendedores
    with tabs[1]:
        vendedores = st.session_state.session_data.get("vendedores", [])
        if vendedores:
            for i, vend in enumerate(vendedores, 1):
                nome = vend.get('nome_completo', vend.get('razao_social', 'N/A'))
                with st.expander(f"Vendedor {i}: {nome}", expanded=True):
                    st.json(vend)
        else:
            st.info("Nenhum vendedor cadastrado ainda")

    # Tab 3: Certidões
    with tabs[2]:
        certidoes = st.session_state.session_data.get("certidoes", [])
        if certidoes:
            for i, cert in enumerate(certidoes, 1):
                if isinstance(cert, dict):
                    tipo = cert.get('tipo', 'N/A')
                    dispensada = "⏭️ Dispensada" if cert.get('dispensada', False) else "✅ Apresentada"
                    with st.expander(f"{i}. {tipo} - {dispensada}", expanded=False):
                        st.json(cert)
                else:
                    st.write(f"{i}. {cert}")
        else:
            st.info("Nenhuma certidão registrada ainda")

    # Tab 4: Histórico
    with tabs[3]:
        if st.session_state.history:
            for entry in reversed(st.session_state.history):
                st.markdown(f"**{entry['timestamp']}** - {entry['action']}")
                st.markdown(f"  └─ {entry['details']}")
        else:
            st.info("Nenhuma ação registrada ainda")

def main():
    """Main application"""
    # Initialize
    init_session_state()

    # Header
    st.markdown('<div class="main-header">📝 Sistema de Escrituras</div>', unsafe_allow_html=True)
    st.markdown("### Interface Interativa para Testes do Fluxo Completo")

    # Render sidebar
    render_sidebar()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Current step
        render_current_step()

    with col2:
        # Quick info
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### ℹ️ Informações")
        st.markdown(f"""
        - **Steps Executados:** {len(st.session_state.history)}
        - **Compradores:** {len(st.session_state.session_data.get('compradores', []))}
        - **Vendedores:** {len(st.session_state.session_data.get('vendedores', []))}
        - **Certidões:** {len(st.session_state.session_data.get('certidoes', []))}
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # Data view
    render_data_view()

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: gray; font-size: 0.9rem;">'
        'Sistema de Escrituras v3.0 | Desenvolvido com Streamlit | 2025'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
