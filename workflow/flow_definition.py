"""Declarative workflow definition - Single source of truth for the complete flow"""
from workflow.state_machine import WorkflowStateMachine, StepDefinition, StepType, TransitionCondition
from workflow.handlers.base_handlers import QuestionHandler, TextInputHandler, FileUploadHandler, DynamicQuestionHandler, CallbackQuestionHandler
from workflow.handlers import document_processors
from models.session import finalize_and_add_comprador, finalize_and_add_vendedor, ensure_temp_data
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER CALLBACKS
# ============================================================================

async def dispensar_certidao(session: Dict[str, Any], tipo: str, vendedor_specific: bool = False):
    """Save certidão as dispensed (not presented)

    Args:
        session: Current session
        tipo: Certificate type (e.g., "negativa_federal", "onus")
        vendedor_specific: If True, append vendedor_index to key
    """
    from models.session import add_certidao_to_session, ensure_temp_data

    # Get vendedor index if needed
    vendedor_index = None
    if vendedor_specific:
        temp_data = ensure_temp_data(session)
        vendedor_index = temp_data.get("current_vendedor_index", 0)

    # Save as dispensed with minimal data
    add_certidao_to_session(
        session,
        tipo=tipo,
        data={},
        vendedor_index=vendedor_index,
        dispensada=True
    )

    logger.info(f"Certidão dispensada: {tipo}" + (f" (vendedor {vendedor_index})" if vendedor_specific else ""))


async def finalize_comprador(session: Dict[str, Any]):
    """Finalize current comprador - move from temp_data to compradores list"""
    finalize_and_add_comprador(session)

    # Clear additional temp fields
    temp_data = ensure_temp_data(session)
    temp_data["documento_tipo"] = None
    temp_data["tipo_pessoa"] = None
    temp_data["conjuge_doc_tipo"] = None

    current_comprador = session.get("compradores", [])[-1] if session.get("compradores") else None
    if current_comprador:
        logger.info(f"Finalized comprador: {current_comprador.get('nome_completo', 'Unknown')}")


async def finalize_vendedor(session: Dict[str, Any]):
    """Finalize current vendedor - move from temp_data to vendedores list"""
    finalize_and_add_vendedor(session)

    # Store vendedor index for certidões
    temp_data = ensure_temp_data(session)
    vendedor_index = len(session.get("vendedores", [])) - 1
    temp_data["current_vendedor_index"] = vendedor_index

    # Clear additional temp fields
    temp_data["documento_tipo"] = None
    temp_data["tipo_pessoa"] = None
    temp_data["conjuge_doc_tipo"] = None
    temp_data["vendedor_possui_certidoes"] = None

    current_vendedor = session.get("vendedores", [])[-1] if session.get("vendedores") else None
    if current_vendedor:
        logger.info(f"Finalized vendedor: {current_vendedor.get('nome_completo', 'Unknown')}")


# ============================================================================
# DRY HELPER FOR CERTIDÃO OPTION WORKFLOW
# ============================================================================

def create_certidao_option_workflow(
    machine: WorkflowStateMachine,
    certidao_tipo: str,
    certidao_display_name: str,
    processor: callable,
    next_step_after: str,
    vendedor_specific: bool = False
) -> str:
    """DRY helper to create option workflow for certidões.

    Creates two steps:
    1. certidao_X_option - asks "Apresentar ou Dispensar?"
    2. certidao_X_upload - file upload with processor (if "Apresentar")

    Args:
        machine: WorkflowStateMachine instance
        certidao_tipo: Internal type name (e.g., "negativa_federal")
        certidao_display_name: Display name (e.g., "Certidão Negativa Federal")
        processor: Async function to process file
        next_step_after: Step to go to after this certidão is done
        vendedor_specific: If True, certidão is vendedor-specific

    Returns:
        Name of the option step (to use as entry point)
    """
    option_step_name = f"certidao_{certidao_tipo}_option"
    upload_step_name = f"certidao_{certidao_tipo}_upload"

    # Create callback for "Dispensar" option
    async def on_dispensar(session):
        await dispensar_certidao(session, certidao_tipo, vendedor_specific)

    # STEP 1: Option question
    machine.register_step(StepDefinition(
        name=option_step_name,
        step_type=StepType.QUESTION,
        handler=CallbackQuestionHandler(
            step_name=option_step_name,
            question=f"Deseja apresentar {certidao_display_name}?",
            options=["Sim", "Não"],
            save_to=None,  # Don't save this response
            on_yes=None,  # "Sim" = go to upload
            on_no=on_dispensar  # "Não" = save as dispensed
        ),
        transitions=[
            (TransitionCondition.IF_YES, upload_step_name),  # "Sim" → upload
            (TransitionCondition.IF_NO, next_step_after)      # "Não" → skip to next
        ]
    ))

    # STEP 2: Upload step
    machine.register_step(StepDefinition(
        name=upload_step_name,
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name=upload_step_name,
            question=f"Faça upload da {certidao_display_name}:",
            file_description="PDF ou imagem da certidão",
            processor=processor
        ),
        next_step=next_step_after
    ))

    logger.debug(f"Created certidão option workflow: {option_step_name} → {upload_step_name} → {next_step_after}")

    return option_step_name


def create_workflow() -> WorkflowStateMachine:
    """Create and configure the complete workflow state machine

    This is the SINGLE SOURCE OF TRUTH for the entire workflow.
    All steps, transitions, and logic are defined here declaratively.
    """
    machine = WorkflowStateMachine()

    # =============================================================================
    # STEP 1: Tipo de Escritura
    # =============================================================================
    machine.register_step(StepDefinition(
        name="tipo_escritura",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="tipo_escritura",
            question="Selecione o tipo de escritura:",
            options=[
                "Escritura de Lote",
                "Escritura de Apto",
                "Escritura Rural",
                "Escritura Rural com Desmembramento de Área"
            ],
            save_to="tipo_escritura"
        ),
        next_step="comprador_tipo"  # Always goes to comprador_tipo
    ))

    # =============================================================================
    # COMPRADORES FLOW
    # =============================================================================

    # STEP 2: Comprador Tipo (Física/Jurídica)
    machine.register_step(StepDefinition(
        name="comprador_tipo",
        step_type=StepType.QUESTION,
        handler=DynamicQuestionHandler(
            step_name="comprador_tipo",
            question_template="Tipo do {count}º comprador:",
            options=["Pessoa Física", "Pessoa Jurídica"],
            count_from="compradores",
            save_to="temp_data.tipo_pessoa"
        ),
        transitions=[
            (TransitionCondition.IF_FISICA, "comprador_documento_tipo"),
            (TransitionCondition.IF_JURIDICA, "comprador_empresa_upload")
        ]
    ))

    # STEP 3a: Comprador Documento Tipo (if Física)
    machine.register_step(StepDefinition(
        name="comprador_documento_tipo",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="comprador_documento_tipo",
            question="Qual documento será apresentado?",
            options=["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            save_to="temp_data.documento_tipo"
        ),
        next_step="comprador_documento_upload"
    ))

    # STEP 3b: Comprador Empresa Upload (if Jurídica)
    machine.register_step(StepDefinition(
        name="comprador_empresa_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="comprador_empresa_upload",
            question="Faça upload do documento da empresa (Cartão CNPJ ou Contrato Social):",
            file_description="PDF ou imagem do documento da empresa",
            processor=document_processors.process_empresa_comprador
        ),
        next_step="comprador_casado"
    ))

    # STEP 4: Comprador Documento Upload
    machine.register_step(StepDefinition(
        name="comprador_documento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="comprador_documento_upload",
            question="Faça upload do documento do comprador:",
            file_description="PDF ou imagem do documento selecionado",
            processor=document_processors.process_documento_comprador
        ),
        next_step="comprador_casado"
    ))

    # STEP 5: Comprador Casado?
    machine.register_step(StepDefinition(
        name="comprador_casado",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="comprador_casado",
            question="O comprador é casado?",
            options=["Sim", "Não"],
            save_to="temp_data.current_comprador.casado"
        ),
        transitions=[
            (TransitionCondition.IF_YES, "certidao_casamento_upload"),
            (TransitionCondition.IF_NO, "comprador_certidao_nascimento_upload")
        ]
    ))

    # STEP 5a: Certidão de Nascimento do Comprador (if solteiro)
    machine.register_step(StepDefinition(
        name="comprador_certidao_nascimento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="comprador_certidao_nascimento_upload",
            question="Faça upload da certidão de nascimento do comprador:",
            file_description="PDF ou imagem da certidão de nascimento",
            processor=document_processors.process_certidao_nascimento
        ),
        next_step="mais_compradores"
    ))

    # STEP 6: Certidão de Casamento Upload (if casado)
    machine.register_step(StepDefinition(
        name="certidao_casamento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_casamento_upload",
            question="Faça upload da certidão de casamento:",
            file_description="PDF ou imagem da certidão de casamento",
            processor=document_processors.process_certidao_casamento
        ),
        next_step="conjuge_assina"
    ))

    # STEP 7: Cônjuge Assina?
    machine.register_step(StepDefinition(
        name="conjuge_assina",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="conjuge_assina",
            question="O cônjuge assina o documento?",
            options=["Sim", "Não"],
            save_to="temp_data.current_comprador.conjuge_assina"
        ),
        transitions=[
            (TransitionCondition.IF_YES, "conjuge_documento_tipo"),
            (TransitionCondition.IF_NO, "mais_compradores")
        ]
    ))

    # STEP 8: Cônjuge Documento Tipo
    machine.register_step(StepDefinition(
        name="conjuge_documento_tipo",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="conjuge_documento_tipo",
            question="Qual documento do cônjuge será apresentado?",
            options=["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            save_to="temp_data.conjuge_doc_tipo"
        ),
        next_step="conjuge_documento_upload"
    ))

    # STEP 9: Cônjuge Documento Upload
    machine.register_step(StepDefinition(
        name="conjuge_documento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="conjuge_documento_upload",
            question="Faça upload do documento do cônjuge:",
            file_description="PDF ou imagem do documento selecionado",
            processor=document_processors.process_documento_conjuge
        ),
        next_step="mais_compradores"
    ))

    # STEP 10: Mais Compradores?
    machine.register_step(StepDefinition(
        name="mais_compradores",
        step_type=StepType.QUESTION,
        handler=CallbackQuestionHandler(
            step_name="mais_compradores",
            question="Tem mais compradores?",
            options=["Sim", "Não"],
            save_to=None,  # Don't save this response
            on_yes=finalize_comprador,  # Finalize current comprador before looping
            on_no=finalize_comprador    # Finalize before moving to vendedores
        ),
        transitions=[
            (TransitionCondition.IF_YES, "comprador_tipo"),  # Loop back
            (TransitionCondition.IF_NO, "vendedor_tipo")     # Move to vendedores
        ]
    ))

    # =============================================================================
    # VENDEDORES FLOW (Similar structure to compradores)
    # =============================================================================

    machine.register_step(StepDefinition(
        name="vendedor_tipo",
        step_type=StepType.QUESTION,
        handler=DynamicQuestionHandler(
            step_name="vendedor_tipo",
            question_template="Tipo do {count}º vendedor:",
            options=["Pessoa Física", "Pessoa Jurídica"],
            count_from="vendedores",
            save_to="temp_data.tipo_pessoa"
        ),
        transitions=[
            (TransitionCondition.IF_FISICA, "vendedor_documento_tipo"),
            (TransitionCondition.IF_JURIDICA, "vendedor_empresa_upload")
        ]
    ))

    # Vendedor Documento Tipo (if Física)
    machine.register_step(StepDefinition(
        name="vendedor_documento_tipo",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="vendedor_documento_tipo",
            question="Qual documento será apresentado?",
            options=["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            save_to="temp_data.documento_tipo"
        ),
        next_step="vendedor_documento_upload"
    ))

    # Vendedor Empresa Upload (if Jurídica)
    machine.register_step(StepDefinition(
        name="vendedor_empresa_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="vendedor_empresa_upload",
            question="Faça upload do documento da empresa vendedora:",
            file_description="PDF ou imagem do CNPJ ou Contrato Social",
            processor=document_processors.process_empresa_vendedor
        ),
        next_step="certidao_negativa_federal_option"  # PJ goes directly to certidões
    ))

    # Vendedor Documento Upload
    machine.register_step(StepDefinition(
        name="vendedor_documento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="vendedor_documento_upload",
            question="Faça upload do documento do vendedor:",
            file_description="PDF ou imagem do documento selecionado",
            processor=document_processors.process_documento_vendedor
        ),
        next_step="vendedor_casado"
    ))

    # Vendedor Casado?
    machine.register_step(StepDefinition(
        name="vendedor_casado",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="vendedor_casado",
            question="O vendedor é casado?",
            options=["Sim", "Não"],
            save_to="temp_data.current_vendedor.casado"
        ),
        transitions=[
            (TransitionCondition.IF_YES, "vendedor_certidao_casamento_upload"),
            (TransitionCondition.IF_NO, "vendedor_certidao_nascimento_upload")
        ]
    ))

    # Vendedor Certidão de Nascimento (if solteiro)
    machine.register_step(StepDefinition(
        name="vendedor_certidao_nascimento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="vendedor_certidao_nascimento_upload",
            question="Faça upload da certidão de nascimento do vendedor:",
            file_description="PDF ou imagem da certidão de nascimento",
            processor=document_processors.process_certidao_nascimento
        ),
        next_step="certidao_negativa_federal_option"
    ))

    # Vendedor Certidão Casamento Upload
    machine.register_step(StepDefinition(
        name="vendedor_certidao_casamento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="vendedor_certidao_casamento_upload",
            question="Faça upload da certidão de casamento do vendedor:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_casamento
        ),
        next_step="vendedor_conjuge_assina"
    ))

    # Vendedor Cônjuge Assina?
    machine.register_step(StepDefinition(
        name="vendedor_conjuge_assina",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="vendedor_conjuge_assina",
            question="O cônjuge do vendedor assina o documento?",
            options=["Sim", "Não"],
            save_to="temp_data.current_vendedor.conjuge_assina"
        ),
        transitions=[
            (TransitionCondition.IF_YES, "vendedor_conjuge_documento_tipo"),
            (TransitionCondition.IF_NO, "certidao_negativa_federal_option")  # Updated
        ]
    ))

    # Vendedor Cônjuge Documento Tipo
    machine.register_step(StepDefinition(
        name="vendedor_conjuge_documento_tipo",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="vendedor_conjuge_documento_tipo",
            question="Qual documento do cônjuge será apresentado?",
            options=["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            save_to="temp_data.conjuge_doc_tipo"
        ),
        next_step="vendedor_conjuge_documento_upload"
    ))

    # Vendedor Cônjuge Documento Upload
    machine.register_step(StepDefinition(
        name="vendedor_conjuge_documento_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="vendedor_conjuge_documento_upload",
            question="Faça upload do documento do cônjuge do vendedor:",
            file_description="PDF ou imagem do documento",
            processor=document_processors.process_vendedor_conjuge_documento
        ),
        next_step="certidao_conjuge_negativa_federal_option"
    ))

    # =============================================================================
    # CERTIDÕES NEGATIVAS DO CÔNJUGE DO VENDEDOR (with option workflow)
    # =============================================================================

    # Federal → Estadual → Municipal → Trabalhista → certidões do vendedor
    create_certidao_option_workflow(
        machine,
        certidao_tipo="conjuge_negativa_trabalhista",
        certidao_display_name="Certidão Negativa Trabalhista do Cônjuge",
        processor=document_processors.process_certidao_negativa_trabalhista,
        next_step_after="certidao_negativa_federal_option",  # Goes to vendor certidões
        vendedor_specific=False  # Cônjuge specific
    )

    create_certidao_option_workflow(
        machine,
        certidao_tipo="conjuge_negativa_municipal",
        certidao_display_name="Certidão Negativa Municipal do Cônjuge",
        processor=document_processors.process_certidao_negativa_municipal,
        next_step_after="certidao_conjuge_negativa_trabalhista_option",
        vendedor_specific=False
    )

    create_certidao_option_workflow(
        machine,
        certidao_tipo="conjuge_negativa_estadual",
        certidao_display_name="Certidão Negativa Estadual do Cônjuge",
        processor=document_processors.process_certidao_negativa_estadual,
        next_step_after="certidao_conjuge_negativa_municipal_option",
        vendedor_specific=False
    )

    # Entry point for cônjuge certidões (from vendedor_conjuge_documento_upload)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="conjuge_negativa_federal",
        certidao_display_name="Certidão Negativa Federal do Cônjuge",
        processor=document_processors.process_certidao_negativa_federal,
        next_step_after="certidao_conjuge_negativa_estadual_option",
        vendedor_specific=False
    )

    # =============================================================================
    # CERTIDÕES NEGATIVAS DO VENDEDOR (with option workflow)
    # =============================================================================

    # Federal → Estadual → Municipal → Trabalhista → mais_vendedores
    create_certidao_option_workflow(
        machine,
        certidao_tipo="negativa_trabalhista",
        certidao_display_name="Certidão Negativa Trabalhista",
        processor=document_processors.process_certidao_negativa_trabalhista,
        next_step_after="mais_vendedores",
        vendedor_specific=True
    )

    create_certidao_option_workflow(
        machine,
        certidao_tipo="negativa_municipal",
        certidao_display_name="Certidão Negativa Municipal",
        processor=document_processors.process_certidao_negativa_municipal,
        next_step_after="certidao_negativa_trabalhista_option",
        vendedor_specific=True
    )

    create_certidao_option_workflow(
        machine,
        certidao_tipo="negativa_estadual",
        certidao_display_name="Certidão Negativa Estadual",
        processor=document_processors.process_certidao_negativa_estadual,
        next_step_after="certidao_negativa_municipal_option",
        vendedor_specific=True
    )

    # Entry point for vendedor certidões (from vendedor_casado or vendedor_conjuge_documento_upload)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="negativa_federal",
        certidao_display_name="Certidão Negativa Federal",
        processor=document_processors.process_certidao_negativa_federal,
        next_step_after="certidao_negativa_estadual_option",
        vendedor_specific=True
    )

    # Mais Vendedores?
    machine.register_step(StepDefinition(
        name="mais_vendedores",
        step_type=StepType.QUESTION,
        handler=CallbackQuestionHandler(
            step_name="mais_vendedores",
            question="Tem mais vendedores?",
            options=["Sim", "Não"],
            save_to=None,
            on_yes=finalize_vendedor,  # Finalize current vendedor before looping
            on_no=finalize_vendedor    # Finalize before moving to certidões
        ),
        transitions=[
            (TransitionCondition.IF_YES, "vendedor_tipo"),
            (TransitionCondition.IF_NO, "check_tipo_escritura_certidoes")  # Check urban vs rural
        ]
    ))

    # =============================================================================
    # CONDITIONAL: URBAN vs RURAL CERTIDÕES
    # =============================================================================

    # Check if escritura is rural
    machine.register_step(StepDefinition(
        name="check_tipo_escritura_certidoes",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="check_tipo_escritura_certidoes",
            question="O imóvel é rural?",
            options=["Sim", "Não"],
            save_to=None  # Don't save, we already have tipo_escritura
        ),
        transitions=[
            (TransitionCondition.IF_YES, "certidao_itr_option"),  # Rural → ITR
            (TransitionCondition.IF_NO, "certidao_matricula_option")  # Urbano → matricula
        ]
    ))

    # =============================================================================
    # CERTIDÕES RURAIS (property-level, with option workflow)
    # =============================================================================

    # ITR - Imposto Territorial Rural (property-level)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="itr",
        certidao_display_name="ITR - Imposto Territorial Rural",
        processor=document_processors.process_certidao_itr,
        next_step_after="certidao_ccir_option",
        vendedor_specific=False  # Property-level
    )

    # CCIR - Certificado de Cadastro de Imóvel Rural (property-level)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="ccir",
        certidao_display_name="CCIR - Certificado de Cadastro de Imóvel Rural",
        processor=document_processors.process_certidao_ccir,
        next_step_after="certidao_incra_option",
        vendedor_specific=False  # Property-level
    )

    # INCRA - Certidão Negativa INCRA (property-level)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="incra",
        certidao_display_name="Certidão Negativa INCRA",
        processor=document_processors.process_certidao_incra,
        next_step_after="certidao_ibama_option",
        vendedor_specific=False  # Property-level
    )

    # IBAMA - Certidão Negativa IBAMA (property-level)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="ibama",
        certidao_display_name="Certidão Negativa IBAMA",
        processor=document_processors.process_certidao_ibama,
        next_step_after="check_desmembramento",
        vendedor_specific=False  # Property-level
    )

    # Check if has desmembramento
    machine.register_step(StepDefinition(
        name="check_desmembramento",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="check_desmembramento",
            question="A escritura rural possui desmembramento de área?",
            options=["Sim", "Não"],
            save_to=None
        ),
        transitions=[
            (TransitionCondition.IF_YES, "certidao_art_desmembramento_option"),
            (TransitionCondition.IF_NO, "valor_imovel")
        ]
    ))

    # ART de Desmembramento (for rural desmembramento) - with option
    create_certidao_option_workflow(
        machine,
        certidao_tipo="art_desmembramento",
        certidao_display_name="ART de Desmembramento",
        processor=document_processors.process_art_desmembramento,
        next_step_after="certidao_planta_desmembramento_option",
        vendedor_specific=False  # Property-level
    )

    # Planta de Desmembramento (for rural desmembramento) - with option
    create_certidao_option_workflow(
        machine,
        certidao_tipo="planta_desmembramento",
        certidao_display_name="Planta de Desmembramento",
        processor=document_processors.process_planta_desmembramento,
        next_step_after="valor_imovel",
        vendedor_specific=False  # Property-level
    )

    # =============================================================================
    # CERTIDÕES URBANAS (property-level, with option workflow)
    # =============================================================================

    # Matrícula do Imóvel (property-level) - documento base
    create_certidao_option_workflow(
        machine,
        certidao_tipo="matricula",
        certidao_display_name="Matrícula do Imóvel",
        processor=document_processors.process_certidao_matricula,
        next_step_after="certidao_iptu_option",
        vendedor_specific=False  # Property-level
    )

    # IPTU (property-level) - imposto
    create_certidao_option_workflow(
        machine,
        certidao_tipo="iptu",
        certidao_display_name="Certidão de IPTU",
        processor=document_processors.process_certidao_iptu,
        next_step_after="certidao_onus_option",
        vendedor_specific=False  # Property-level
    )

    # Certidão de Ônus Reais (property-level)
    create_certidao_option_workflow(
        machine,
        certidao_tipo="onus",
        certidao_display_name="Certidão de Ônus Reais",
        processor=document_processors.process_certidao_onus,
        next_step_after="check_tipo_escritura_condominio",
        vendedor_specific=False  # Property-level
    )

    # Check if Apto needs condomínio certidão
    machine.register_step(StepDefinition(
        name="check_tipo_escritura_condominio",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="check_tipo_escritura_condominio",
            question="O imóvel é Apartamento (possui certidão de condomínio)?",
            options=["Sim", "Não"],
            save_to=None
        ),
        transitions=[
            (TransitionCondition.IF_YES, "certidao_condominio_option"),  # Updated
            (TransitionCondition.IF_NO, "valor_imovel")
        ]
    ))

    # Certidão Condomínio (for Apto) - with option workflow
    create_certidao_option_workflow(
        machine,
        certidao_tipo="condominio",
        certidao_display_name="Certidão de Condomínio",
        processor=document_processors.process_certidao_condominio,
        next_step_after="certidao_objeto_pe_option",
        vendedor_specific=False  # Property-level
    )

    # Certidão de Objeto e Pé (for Apto) - with option workflow
    create_certidao_option_workflow(
        machine,
        certidao_tipo="objeto_pe",
        certidao_display_name="Certidão de Objeto e Pé",
        processor=document_processors.process_certidao_objeto_pe,
        next_step_after="valor_imovel",
        vendedor_specific=False  # Property-level
    )

    # =============================================================================
    # PAYMENT FLOW
    # =============================================================================

    machine.register_step(StepDefinition(
        name="valor_imovel",
        step_type=StepType.TEXT_INPUT,
        handler=TextInputHandler(
            step_name="valor_imovel",
            question="Informe o valor do imóvel (ex: R$ 250.000,00):",
            save_to="valor",
            placeholder="R$ 0,00"
        ),
        next_step="forma_pagamento"
    ))

    machine.register_step(StepDefinition(
        name="forma_pagamento",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="forma_pagamento",
            question="Forma de pagamento:",
            options=["À VISTA", "ANTERIORMENTE"],
            save_to="forma_pagamento"
        ),
        next_step="meio_pagamento"
    ))

    machine.register_step(StepDefinition(
        name="meio_pagamento",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="meio_pagamento",
            question="Meio de pagamento:",
            options=["transferência bancária/pix", "dinheiro", "cheque"],
            save_to="meio_pagamento"
        ),
        next_step="processing"
    ))

    # =============================================================================
    # FINAL PROCESSING
    # =============================================================================

    machine.register_step(StepDefinition(
        name="processing",
        step_type=StepType.PROCESSING,
        handler=QuestionHandler(  # Placeholder
            step_name="processing",
            question="Processando documentos e gerando escritura...",
            options=[],
            save_to=None
        ),
        next_step=None  # End of workflow
    ))

    # Set initial step
    machine.set_initial_step("tipo_escritura")

    logger.info(f"Workflow created with {len(machine.steps)} steps")

    return machine


# Global instance (singleton)
_workflow_instance = None


def get_workflow() -> WorkflowStateMachine:
    """Get the global workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = create_workflow()
    return _workflow_instance


def visualize_workflow():
    """Print workflow visualization"""
    workflow = get_workflow()
    print(workflow.visualize_workflow())


if __name__ == "__main__":
    # Generate workflow map
    visualize_workflow()
