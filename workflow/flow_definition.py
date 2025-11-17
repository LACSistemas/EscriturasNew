"""Declarative workflow definition - Single source of truth for the complete flow"""
from workflow.state_machine import WorkflowStateMachine, StepDefinition, StepType, TransitionCondition
from workflow.handlers.base_handlers import QuestionHandler, TextInputHandler, DynamicQuestionHandler
import logging

logger = logging.getLogger(__name__)


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
    # TODO: Implement FileUploadHandler with CNPJ processor
    # machine.register_step(...)

    # STEP 4: Comprador Documento Upload
    # TODO: Implement FileUploadHandler with OCR+AI processor
    # machine.register_step(...)

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
    # TODO: Implement FileUploadHandler
    # machine.register_step(...)

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
    # TODO: Implement FileUploadHandler
    # machine.register_step(...)

    # STEP 10: Mais Compradores?
    machine.register_step(StepDefinition(
        name="mais_compradores",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="mais_compradores",
            question="Tem mais compradores?",
            options=["Sim", "Não"],
            save_to=None  # Don't save this response
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

    # ... (similar steps for vendedores)

    machine.register_step(StepDefinition(
        name="mais_vendedores",
        step_type=StepType.QUESTION,
        handler=QuestionHandler(
            step_name="mais_vendedores",
            question="Tem mais vendedores?",
            options=["Sim", "Não"],
            save_to=None
        ),
        transitions=[
            (TransitionCondition.IF_YES, "vendedor_tipo"),
            (TransitionCondition.IF_NO, "certidao_onus_upload")
        ]
    ))

    # =============================================================================
    # CERTIDÕES FLOW
    # =============================================================================

    # ... (certidoes steps)

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
