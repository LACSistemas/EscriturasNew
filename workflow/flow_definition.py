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
            (TransitionCondition.IF_NO, "mais_compradores")
        ]
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
        next_step="vendedor_casado"
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
            (TransitionCondition.IF_NO, "certidoes_vendedor_pergunta")
        ]
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
            (TransitionCondition.IF_NO, "certidoes_vendedor_pergunta")
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
        next_step="certidoes_vendedor_pergunta"
    ))

    # Certidões do Vendedor - Pergunta
    machine.register_step(StepDefinition(
        name="certidoes_vendedor_pergunta",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="certidoes_vendedor_pergunta",
            question="O vendedor possui certidões negativas?",
            options=["Sim", "Não, dispensar certidões"],
            save_to="temp_data.vendedor_possui_certidoes"
        ),
        transitions=[
            (TransitionCondition.IF_YES, "certidao_negativa_federal_upload"),
            (TransitionCondition.IF_NO, "mais_vendedores")
        ]
    ))

    # Certidão Negativa Federal Upload
    machine.register_step(StepDefinition(
        name="certidao_negativa_federal_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_negativa_federal_upload",
            question="Faça upload da Certidão Negativa Federal:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_negativa_federal
        ),
        next_step="certidao_negativa_estadual_upload"
    ))

    # Certidão Negativa Estadual Upload
    machine.register_step(StepDefinition(
        name="certidao_negativa_estadual_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_negativa_estadual_upload",
            question="Faça upload da Certidão Negativa Estadual:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_negativa_estadual
        ),
        next_step="certidao_negativa_municipal_upload"
    ))

    # Certidão Negativa Municipal Upload
    machine.register_step(StepDefinition(
        name="certidao_negativa_municipal_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_negativa_municipal_upload",
            question="Faça upload da Certidão Negativa Municipal:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_negativa_municipal
        ),
        next_step="certidao_negativa_trabalhista_upload"
    ))

    # Certidão Negativa Trabalhista Upload
    machine.register_step(StepDefinition(
        name="certidao_negativa_trabalhista_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_negativa_trabalhista_upload",
            question="Faça upload da Certidão Negativa Trabalhista:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_negativa_trabalhista
        ),
        next_step="mais_vendedores"
    ))

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
            (TransitionCondition.IF_NO, "certidao_onus_upload")
        ]
    ))

    # =============================================================================
    # CERTIDÕES FLOW
    # =============================================================================

    # Certidão de Ônus Reais Upload (property-level)
    machine.register_step(StepDefinition(
        name="certidao_onus_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_onus_upload",
            question="Faça upload da Certidão de Ônus Reais do imóvel:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_onus
        ),
        next_step="check_tipo_escritura_condominio"
    ))

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
            (TransitionCondition.IF_YES, "certidao_condominio_upload"),
            (TransitionCondition.IF_NO, "valor_imovel")
        ]
    ))

    # Certidão Condomínio (for Apto)
    machine.register_step(StepDefinition(
        name="certidao_condominio_upload",
        step_type=StepType.FILE_UPLOAD,
        handler=FileUploadHandler(
            step_name="certidao_condominio_upload",
            question="Faça upload da Certidão de Condomínio:",
            file_description="PDF ou imagem da certidão",
            processor=document_processors.process_certidao_condominio
        ),
        next_step="valor_imovel"
    ))

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
