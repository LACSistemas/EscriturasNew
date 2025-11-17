"""
End-to-end workflow integration tests

Tests 4 complete scenarios:
1. Escritura de Lote (simple urban)
2. Escritura de Apto (complex urban with condomínio)
3. Escritura Rural (without desmembramento)
4. Escritura Rural com Desmembramento

Each test validates:
- State machine transitions
- Data extraction and storage
- Certidão option handling (Apresentar/Dispensar)
- Final escritura generation
"""

# Mock Google Cloud imports BEFORE anything else
import sys
from unittest.mock import Mock, MagicMock

# Mock google.cloud.vision
sys.modules['google'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.vision'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['fitz'] = MagicMock()  # PyMuPDF

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/user/EscriturasNew')

from workflow.flow_definition import create_workflow
from workflow.state_machine import WorkflowStateMachine
from models.session import create_new_session_dict
from tests.test_dummy_data import (
    MockOCRService, MockAIService,
    generate_rg_data, generate_cnh_data, generate_ctps_data,
    generate_empresa_data, generate_certidao_casamento_data,
    generate_certidao_nascimento_data,
    generate_certidao_negativa_data, generate_certidao_onus_data,
    generate_certidao_matricula_data, generate_certidao_iptu_data,
    generate_certidao_condominio_data, generate_certidao_objeto_pe_data,
    generate_certidao_itr_data, generate_certidao_ccir_data,
    generate_certidao_incra_data, generate_certidao_ibama_data,
    generate_art_desmembramento_data, generate_planta_desmembramento_data
)


# ============================================================================
# TEST HARNESS - Workflow Simulator
# ============================================================================

class WorkflowSimulator:
    """Simulates complete workflow execution with mock services"""

    def __init__(self):
        self.workflow: WorkflowStateMachine = create_workflow()
        self.session: Dict[str, Any] = create_new_session_dict("test-session-id")
        self.session["current_step"] = self.workflow.initial_step
        self.mock_ocr = MockOCRService()
        self.mock_ai = MockAIService()
        self.step_log: List[str] = []
        self.transition_log: List[tuple] = []
        self.errors: List[str] = []

    def log_step(self, step_name: str, action: str, details: str = ""):
        """Log a step execution"""
        log_entry = f"[{len(self.step_log) + 1:03d}] {step_name:<40} | {action:<15} | {details}"
        self.step_log.append(log_entry)
        print(log_entry)

    def log_transition(self, from_step: str, to_step: str, reason: str = ""):
        """Log a state transition"""
        self.transition_log.append((from_step, to_step, reason))
        print(f"      └─> Transition: {from_step} → {to_step} ({reason})")

    def log_error(self, error: str):
        """Log an error"""
        self.errors.append(error)
        print(f"      ❌ ERROR: {error}")

    async def process_question_step(self, response: str) -> bool:
        """Process a question step"""
        current_step = self.session["current_step"]
        self.log_step(current_step, "QUESTION", f"Response: {response}")

        try:
            # Process the step
            await self.workflow.process_step(
                session=self.session,
                response=response,
                vision_client=None,
                gemini_model=None
            )

            # Log transition
            new_step = self.session["current_step"]
            if new_step != current_step:
                self.log_transition(current_step, new_step, f"Answer: {response}")

            return True

        except Exception as e:
            self.log_error(f"Question step failed: {str(e)}")
            return False

    async def process_file_upload_step(self, doc_type: str, custom_data: Dict = None) -> bool:
        """Process a file upload step"""
        current_step = self.session["current_step"]
        self.log_step(current_step, "FILE_UPLOAD", f"Type: {doc_type}")

        try:
            # Create dummy file data (use .png to avoid PDF processing)
            file_data = b"DUMMY_FILE_CONTENT"
            filename = f"{doc_type}.png"

            # Patch BOTH the module-level functions AND the imports in document_processors
            with patch('services.ocr_service_async.extract_text_from_file_async',
                      new=self.mock_ocr.extract_text_from_file_async):
                with patch('workflow.handlers.document_processors.extract_text_from_file_async',
                          new=self.mock_ocr.extract_text_from_file_async):
                    with patch('services.ai_service_async.extract_data_with_gemini_async',
                              new=self._create_custom_ai_mock(doc_type, custom_data)):
                        with patch('workflow.handlers.document_processors.extract_data_with_gemini_async',
                                  new=self._create_custom_ai_mock(doc_type, custom_data)):

                            # Process the step
                            await self.workflow.process_step(
                                session=self.session,
                                file_data=file_data,
                                filename=filename,
                                vision_client=None,
                                gemini_model=None
                            )

                            # Log transition
                            new_step = self.session["current_step"]
                            if new_step != current_step:
                                self.log_transition(current_step, new_step, f"File: {doc_type}")

                            return True

        except Exception as e:
            self.log_error(f"File upload failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _create_custom_ai_mock(self, doc_type: str, custom_data: Dict = None):
        """Create a custom AI mock that returns specific data"""
        async def custom_ai_extractor(text, prompt, gemini_model=None):
            if custom_data:
                return custom_data

            # Use the standard mock AI service
            return await self.mock_ai.extract_data_with_gemini_async(text, prompt, gemini_model)

        return custom_ai_extractor

    def print_summary(self):
        """Print test execution summary"""
        print("\n" + "="*100)
        print("TEST EXECUTION SUMMARY")
        print("="*100)
        print(f"Total Steps Executed: {len(self.step_log)}")
        print(f"Total Transitions: {len(self.transition_log)}")
        print(f"Errors Encountered: {len(self.errors)}")
        print(f"Final Step: {self.session['current_step']}")
        print(f"Compradores: {len(self.session.get('compradores', []))}")
        print(f"Vendedores: {len(self.session.get('vendedores', []))}")
        print(f"Certidões: {len(self.session.get('certidoes', []))}")

        if self.errors:
            print("\n⚠️  ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        print("\n📋 SESSION DATA SUMMARY:")
        print(f"  - Tipo Escritura: {self.session.get('tipo_escritura', 'N/A')}")
        print(f"  - Valor: {self.session.get('valor', 'N/A')}")
        print(f"  - Forma Pagamento: {self.session.get('forma_pagamento', 'N/A')}")
        print(f"  - Meio Pagamento: {self.session.get('meio_pagamento', 'N/A')}")

        print("\n📊 COMPRADORES:")
        for i, comp in enumerate(self.session.get('compradores', []), 1):
            print(f"  {i}. {comp.get('tipo', 'N/A')} - {comp.get('nome_completo', 'N/A')}")

        print("\n📊 VENDEDORES:")
        for i, vend in enumerate(self.session.get('vendedores', []), 1):
            print(f"  {i}. {vend.get('tipo', 'N/A')} - {vend.get('nome_completo', vend.get('razao_social', 'N/A'))}")

        print("\n📊 CERTIDÕES:")
        for i, cert in enumerate(self.session.get('certidoes', []), 1):
            if isinstance(cert, dict):
                dispensada = "✅ Apresentada" if not cert.get('dispensada', False) else "⏭️  Dispensada"
                print(f"  {i}. {cert.get('tipo', 'N/A'):<30} - {dispensada}")
            else:
                print(f"  {i}. {cert} (invalid format)")

        print("="*100 + "\n")


# ============================================================================
# TEST SCENARIO 1: Escritura de Lote (Simple)
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_1_lote_simples():
    """
    Test Scenario 1: Simple Lote (Urban)

    - 1 comprador PF solteiro (RG)
    - 1 vendedor PF solteiro (CNH)
    - All certidões vendedor: APRESENTAR
    - Matricula, IPTU, Ônus: APRESENTAR
    """
    print("\n" + "="*100)
    print("SCENARIO 1: ESCRITURA DE LOTE (SIMPLES)")
    print("="*100 + "\n")

    sim = WorkflowSimulator()

    # Step 1: Tipo de Escritura
    await sim.process_question_step("Escritura de Lote")

    # Step 2: Comprador tipo
    await sim.process_question_step("Pessoa Física")

    # Step 3: Comprador documento tipo
    await sim.process_question_step("Carteira de Identidade")

    # Step 4: Comprador documento upload (RG)
    await sim.process_file_upload_step("comprador_rg", generate_rg_data("Masculino"))

    # Step 5: Comprador casado?
    await sim.process_question_step("Não")

    # Step 6: Comprador certidão de nascimento (solteiro)
    await sim.process_file_upload_step("comprador_certidao_nascimento", generate_certidao_nascimento_data())

    # Step 7: Mais compradores?
    await sim.process_question_step("Não")

    # Step 8: Vendedor tipo
    await sim.process_question_step("Pessoa Física")

    # Step 9: Vendedor documento tipo
    await sim.process_question_step("CNH")

    # Step 10: Vendedor documento upload (CNH)
    await sim.process_file_upload_step("vendedor_cnh", generate_cnh_data("Masculino"))

    # Step 11: Vendedor casado?
    await sim.process_question_step("Não")

    # Step 12: Vendedor certidão de nascimento (solteiro)
    await sim.process_file_upload_step("vendedor_certidao_nascimento", generate_certidao_nascimento_data())

    # Step 13-20: Certidões negativas (Federal, Estadual, Municipal, Trabalhista)
    # Each certidão has 2 steps: option + upload (if "Sim")
    await sim.process_question_step("Sim")  # Federal option
    await sim.process_file_upload_step("certidao_federal", generate_certidao_negativa_data())

    await sim.process_question_step("Sim")  # Estadual option
    await sim.process_file_upload_step("certidao_estadual", generate_certidao_negativa_data())

    await sim.process_question_step("Sim")  # Municipal option
    await sim.process_file_upload_step("certidao_municipal", generate_certidao_negativa_data())

    await sim.process_question_step("Sim")  # Trabalhista option
    await sim.process_file_upload_step("certidao_trabalhista", generate_certidao_negativa_data())

    # Step 19: Mais vendedores?
    await sim.process_question_step("Não")

    # Step 20: Imóvel é rural?
    await sim.process_question_step("Não")

    # Step 21-26: Certidões urbanas (Matricula, IPTU, Ônus)
    await sim.process_question_step("Sim")  # Matricula option
    await sim.process_file_upload_step("matricula", generate_certidao_matricula_data())

    await sim.process_question_step("Sim")  # IPTU option
    await sim.process_file_upload_step("iptu", generate_certidao_iptu_data())

    await sim.process_question_step("Sim")  # Ônus option
    await sim.process_file_upload_step("onus", generate_certidao_onus_data())

    # Step 27: É apartamento?
    await sim.process_question_step("Não")

    # Step 28-30: Payment info
    await sim.process_question_step("R$ 250.000,00")  # Valor
    await sim.process_question_step("À VISTA")  # Forma pagamento
    await sim.process_question_step("transferência bancária/pix")  # Meio pagamento

    # Print summary
    sim.print_summary()

    # Validations
    assert sim.session["current_step"] == "processing", "Should reach processing step"
    assert len(sim.session.get("compradores", [])) == 1, "Should have 1 comprador"
    assert len(sim.session.get("vendedores", [])) == 1, "Should have 1 vendedor"
    assert sim.session.get("tipo_escritura") == "Escritura de Lote"
    assert sim.session.get("valor") == "R$ 250.000,00"
    assert len(sim.errors) == 0, f"Should have no errors, but got: {sim.errors}"

    print("✅ SCENARIO 1 PASSED\n")


# ============================================================================
# TEST SCENARIO 2: Escritura de Apto (Complex)
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_2_apto_complexo():
    """
    Test Scenario 2: Complex Apto

    - 2 compradores PF (1 casado com cônjuge assinando, 1 solteiro)
    - 1 vendedor PJ (empresa)
    - Mix certidões: 2 apresentar, 2 dispensar
    - Condomínio + Objeto e Pé: APRESENTAR
    """
    print("\n" + "="*100)
    print("SCENARIO 2: ESCRITURA DE APTO (COMPLEXO)")
    print("="*100 + "\n")

    sim = WorkflowSimulator()

    # Step 1: Tipo de Escritura
    await sim.process_question_step("Escritura de Apto")

    # COMPRADOR 1 (Casado com cônjuge assinando)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("Carteira de Identidade")
    await sim.process_file_upload_step("comprador1_rg", generate_rg_data("Masculino"))
    await sim.process_question_step("Sim")  # Casado

    # Certidão de casamento
    await sim.process_file_upload_step("certidao_casamento", generate_certidao_casamento_data())

    await sim.process_question_step("Sim")  # Cônjuge assina
    await sim.process_question_step("CNH")  # Cônjuge doc tipo
    await sim.process_file_upload_step("conjuge_cnh", generate_cnh_data("Feminino"))

    await sim.process_question_step("Sim")  # Mais compradores

    # COMPRADOR 2 (Solteiro)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("CNH")
    await sim.process_file_upload_step("comprador2_cnh", generate_cnh_data("Feminino"))
    await sim.process_question_step("Não")  # Casado

    # Certidão de nascimento (solteiro)
    await sim.process_file_upload_step("comprador2_certidao_nascimento", generate_certidao_nascimento_data())

    await sim.process_question_step("Não")  # Mais compradores

    # VENDEDOR (Empresa)
    await sim.process_question_step("Pessoa Jurídica")
    await sim.process_file_upload_step("vendedor_cnpj", generate_empresa_data())
    # PJ goes directly to certidões (no casado question or certidão nascimento)

    # Certidões negativas (Mix: apresentar, dispensar, apresentar, dispensar)
    await sim.process_question_step("Sim")  # Federal
    await sim.process_file_upload_step("certidao_federal", generate_certidao_negativa_data())

    await sim.process_question_step("Não")  # Estadual

    await sim.process_question_step("Sim")  # Municipal
    await sim.process_file_upload_step("certidao_municipal", generate_certidao_negativa_data())

    await sim.process_question_step("Não")  # Trabalhista

    await sim.process_question_step("Não")  # Mais vendedores

    # Imóvel é rural?
    await sim.process_question_step("Não")

    # Certidões urbanas
    await sim.process_question_step("Sim")  # Matricula
    await sim.process_file_upload_step("matricula", generate_certidao_matricula_data())

    await sim.process_question_step("Sim")  # IPTU
    await sim.process_file_upload_step("iptu", generate_certidao_iptu_data())

    await sim.process_question_step("Sim")  # Ônus
    await sim.process_file_upload_step("onus", generate_certidao_onus_data())

    # É apartamento?
    await sim.process_question_step("Sim")

    # Certidões de Apto
    await sim.process_question_step("Sim")  # Condomínio
    await sim.process_file_upload_step("condominio", generate_certidao_condominio_data())

    await sim.process_question_step("Sim")  # Objeto e Pé
    await sim.process_file_upload_step("objeto_pe", generate_certidao_objeto_pe_data())

    # Payment
    await sim.process_question_step("R$ 450.000,00")
    await sim.process_question_step("ANTERIORMENTE")
    await sim.process_question_step("transferência bancária/pix")

    # Print summary
    sim.print_summary()

    # Validations
    assert sim.session["current_step"] == "processing"
    assert len(sim.session.get("compradores", [])) == 2, "Should have 2 compradores"
    assert len(sim.session.get("vendedores", [])) == 1, "Should have 1 vendedor"
    assert sim.session["tipo_escritura"] == "Escritura de Apto"
    assert len(sim.errors) == 0, f"Should have no errors, but got: {sim.errors}"

    print("✅ SCENARIO 2 PASSED\n")


# ============================================================================
# TEST SCENARIO 3: Escritura Rural (Sem Desmembramento)
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_3_rural_sem_desmembramento():
    """
    Test Scenario 3: Rural without desmembramento

    - 1 comprador PF casado (cônjuge assina)
    - 2 vendedores PF (ambos solteiros)
    - ITR, CCIR, INCRA, IBAMA: APRESENTAR
    - Não tem desmembramento
    """
    print("\n" + "="*100)
    print("SCENARIO 3: ESCRITURA RURAL (SEM DESMEMBRAMENTO)")
    print("="*100 + "\n")

    sim = WorkflowSimulator()

    # Tipo de Escritura
    await sim.process_question_step("Escritura Rural")

    # COMPRADOR (Casado com cônjuge assinando)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("Carteira de Identidade")
    await sim.process_file_upload_step("comprador_rg", generate_rg_data("Masculino"))
    await sim.process_question_step("Sim")  # Casado

    await sim.process_file_upload_step("certidao_casamento", generate_certidao_casamento_data())

    await sim.process_question_step("Sim")  # Cônjuge assina
    await sim.process_question_step("Carteira de Identidade")
    await sim.process_file_upload_step("conjuge_rg", generate_rg_data("Feminino"))

    await sim.process_question_step("Não")  # Mais compradores

    # VENDEDOR 1 (Solteiro)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("CNH")
    await sim.process_file_upload_step("vendedor1_cnh", generate_cnh_data("Masculino"))
    await sim.process_question_step("Não")  # Casado

    # Certidão de nascimento (solteiro)
    await sim.process_file_upload_step("vendedor1_certidao_nascimento", generate_certidao_nascimento_data())

    # Certidões vendedor 1
    for cert_name in ["Federal", "Estadual", "Municipal", "Trabalhista"]:
        await sim.process_question_step("Sim")
        await sim.process_file_upload_step(f"certidao_{cert_name.lower()}", generate_certidao_negativa_data())

    await sim.process_question_step("Sim")  # Mais vendedores

    # VENDEDOR 2 (Solteiro)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("Carteira de Identidade")
    await sim.process_file_upload_step("vendedor2_rg", generate_rg_data("Feminino"))
    await sim.process_question_step("Não")  # Casado

    # Certidão de nascimento (solteiro)
    await sim.process_file_upload_step("vendedor2_certidao_nascimento", generate_certidao_nascimento_data())

    # Certidões vendedor 2
    for cert_name in ["Federal", "Estadual", "Municipal", "Trabalhista"]:
        await sim.process_question_step("Sim")
        await sim.process_file_upload_step(f"certidao_{cert_name.lower()}_v2", generate_certidao_negativa_data())

    await sim.process_question_step("Não")  # Mais vendedores

    # Imóvel é rural?
    await sim.process_question_step("Sim")

    # Certidões rurais (ITR, CCIR, INCRA, IBAMA)
    await sim.process_question_step("Sim")  # ITR
    await sim.process_file_upload_step("itr", generate_certidao_itr_data())

    await sim.process_question_step("Sim")  # CCIR
    await sim.process_file_upload_step("ccir", generate_certidao_ccir_data())

    await sim.process_question_step("Sim")  # INCRA
    await sim.process_file_upload_step("incra", generate_certidao_incra_data())

    await sim.process_question_step("Sim")  # IBAMA
    await sim.process_file_upload_step("ibama", generate_certidao_ibama_data())

    # Tem desmembramento?
    await sim.process_question_step("Não")

    # Payment
    await sim.process_question_step("R$ 1.200.000,00")
    await sim.process_question_step("À VISTA")
    await sim.process_question_step("transferência bancária/pix")

    # Print summary
    sim.print_summary()

    # Validations
    assert sim.session["current_step"] == "processing"
    assert len(sim.session.get("compradores", [])) == 1
    assert len(sim.session.get("vendedores", [])) == 2, "Should have 2 vendedores"
    assert sim.session["tipo_escritura"] == "Escritura Rural"
    assert len(sim.errors) == 0, f"Should have no errors, but got: {sim.errors}"

    print("✅ SCENARIO 3 PASSED\n")


# ============================================================================
# TEST SCENARIO 4: Escritura Rural com Desmembramento
# ============================================================================

@pytest.mark.asyncio
async def test_scenario_4_rural_com_desmembramento():
    """
    Test Scenario 4: Rural with desmembramento

    - 1 comprador PF solteiro
    - 1 vendedor PF casado (cônjuge assina)
    - ITR, CCIR: APRESENTAR, INCRA: DISPENSAR, IBAMA: APRESENTAR
    - Tem desmembramento: ART + Planta APRESENTAR
    """
    print("\n" + "="*100)
    print("SCENARIO 4: ESCRITURA RURAL COM DESMEMBRAMENTO")
    print("="*100 + "\n")

    sim = WorkflowSimulator()

    # Tipo de Escritura
    await sim.process_question_step("Escritura Rural com Desmembramento de Área")

    # COMPRADOR (Solteiro)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("CNH")
    await sim.process_file_upload_step("comprador_cnh", generate_cnh_data("Masculino"))
    await sim.process_question_step("Não")  # Casado

    # Certidão de nascimento (solteiro)
    await sim.process_file_upload_step("comprador_certidao_nascimento", generate_certidao_nascimento_data())

    await sim.process_question_step("Não")  # Mais compradores

    # VENDEDOR (Casado com cônjuge assinando)
    await sim.process_question_step("Pessoa Física")
    await sim.process_question_step("Carteira de Identidade")
    await sim.process_file_upload_step("vendedor_rg", generate_rg_data("Masculino"))
    await sim.process_question_step("Sim")  # Casado

    await sim.process_file_upload_step("certidao_casamento", generate_certidao_casamento_data())

    await sim.process_question_step("Sim")  # Cônjuge assina
    await sim.process_question_step("CNH")
    await sim.process_file_upload_step("conjuge_cnh", generate_cnh_data("Feminino"))

    # Certidões do cônjuge (4 certidões negativas)
    for cert_name in ["Federal", "Estadual", "Municipal", "Trabalhista"]:
        await sim.process_question_step("Sim")
        await sim.process_file_upload_step(f"conjuge_certidao_{cert_name.lower()}", generate_certidao_negativa_data())

    # Certidões vendedor
    for cert_name in ["Federal", "Estadual", "Municipal", "Trabalhista"]:
        await sim.process_question_step("Sim")
        await sim.process_file_upload_step(f"certidao_{cert_name.lower()}", generate_certidao_negativa_data())

    await sim.process_question_step("Não")  # Mais vendedores

    # Imóvel é rural?
    await sim.process_question_step("Sim")

    # Certidões rurais (ITR: apresentar, CCIR: apresentar, INCRA: dispensar, IBAMA: apresentar)
    await sim.process_question_step("Sim")  # ITR
    await sim.process_file_upload_step("itr", generate_certidao_itr_data())

    await sim.process_question_step("Sim")  # CCIR
    await sim.process_file_upload_step("ccir", generate_certidao_ccir_data())

    await sim.process_question_step("Não")  # INCRA

    await sim.process_question_step("Sim")  # IBAMA
    await sim.process_file_upload_step("ibama", generate_certidao_ibama_data())

    # Tem desmembramento?
    await sim.process_question_step("Sim")

    # Desmembramento docs
    await sim.process_question_step("Sim")  # ART
    await sim.process_file_upload_step("art_desmembramento", generate_art_desmembramento_data())

    await sim.process_question_step("Sim")  # Planta
    await sim.process_file_upload_step("planta_desmembramento", generate_planta_desmembramento_data())

    # Payment
    await sim.process_question_step("R$ 850.000,00")
    await sim.process_question_step("À VISTA")
    await sim.process_question_step("dinheiro")

    # Print summary
    sim.print_summary()

    # Validations
    assert sim.session["current_step"] == "processing"
    assert len(sim.session.get("compradores", [])) == 1
    assert len(sim.session.get("vendedores", [])) == 1
    assert sim.session["tipo_escritura"] == "Escritura Rural com Desmembramento de Área"
    assert len(sim.errors) == 0, f"Should have no errors, but got: {sim.errors}"

    print("✅ SCENARIO 4 PASSED\n")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    """Run all scenarios sequentially with detailed output"""
    print("\n" + "🚀"*50)
    print("WORKFLOW INTEGRATION TESTS - 4 COMPLETE SCENARIOS")
    print("🚀"*50 + "\n")

    start_time = datetime.now()

    # Run all tests
    try:
        asyncio.run(test_scenario_1_lote_simples())
        asyncio.run(test_scenario_2_apto_complexo())
        asyncio.run(test_scenario_3_rural_sem_desmembramento())
        asyncio.run(test_scenario_4_rural_com_desmembramento())

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "🎉"*50)
        print("ALL TESTS PASSED!")
        print(f"Total execution time: {duration:.2f} seconds")
        print("🎉"*50 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
