"""Workflow step management"""
from typing import Dict, Any


def get_next_step(session: Dict[str, Any]) -> Dict[str, Any]:
    """Determine the next step in the workflow"""
    step = session["current_step"]
    progress = f"Step {session.get('step_number', 1)} of approximately 15-20"

    # Initial step - tipo de escritura
    if step == "tipo_escritura":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Selecione o tipo de escritura:",
            "options": ["Escritura de Lote", "Escritura de Apto", "Escritura Rural", "Escritura Rural com Desmembramento de Área"],
            "requires_file": False,
            "progress": progress
        }

    # Comprador steps
    elif step == "comprador_tipo":
        count = len(session["compradores"])
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Tipo do {count + 1}º comprador:",
            "options": ["Pessoa Física", "Pessoa Jurídica"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "comprador_documento_tipo":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Qual documento será apresentado?",
            "options": ["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "comprador_documento_upload":
        doc_type = session["temp_data"].get("documento_tipo", "documento")
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Faça upload do(a) {doc_type}:",
            "requires_file": True,
            "file_description": f"Imagem do(a) {doc_type}",
            "progress": progress
        }

    elif step == "comprador_casado":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "O comprador é casado?",
            "options": ["Sim", "Não"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "certidao_casamento_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Casamento:",
            "requires_file": True,
            "file_description": "Certidão de Casamento",
            "progress": progress
        }

    elif step == "conjuge_assina":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "O cônjuge assina o documento?",
            "options": ["Sim", "Não"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "conjuge_documento_tipo":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Qual documento do cônjuge será apresentado?",
            "options": ["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "conjuge_documento_upload":
        doc_type = session["temp_data"].get("conjuge_doc_tipo", "documento")
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Faça upload do(a) {doc_type} do cônjuge:",
            "requires_file": True,
            "file_description": f"Imagem do(a) {doc_type} do cônjuge",
            "progress": progress
        }

    elif step == "mais_compradores":
        current_count = len(session["compradores"]) + (1 if "current_comprador" in session.get("temp_data", {}) else 0)
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Tem mais compradores? (Atualmente: {current_count})",
            "options": ["Sim", "Não"],
            "requires_file": False,
            "progress": progress
        }

    # Similar steps for vendedores
    elif step == "vendedor_tipo":
        count = len(session["vendedores"])
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Tipo do {count + 1}º vendedor:",
            "options": ["Pessoa Física", "Pessoa Jurídica"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "vendedor_documento_tipo":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Qual documento será apresentado?",
            "options": ["Carteira de Identidade", "CNH", "Carteira de Trabalho"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "vendedor_documento_upload":
        doc_type = session["temp_data"].get("documento_tipo", "documento")
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Faça upload do(a) {doc_type}:",
            "requires_file": True,
            "file_description": f"Imagem do(a) {doc_type}",
            "progress": progress
        }

    elif step == "vendedor_casado":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "O vendedor é casado?",
            "options": ["Sim", "Não"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "vendedor_certidao_casamento_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Casamento do vendedor:",
            "requires_file": True,
            "file_description": "Certidão de Casamento do Vendedor",
            "progress": progress
        }

    elif step == "mais_vendedores":
        current_count = len(session["vendedores"]) + (1 if "current_vendedor" in session.get("temp_data", {}) else 0)
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Tem mais vendedores? (Atualmente: {current_count})",
            "options": ["Sim", "Não"],
            "requires_file": False,
            "progress": progress
        }

    # Certidões steps
    elif step == "certidao_onus_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Ônus:",
            "requires_file": True,
            "file_description": "Certidão de Ônus e Ações Reais",
            "progress": progress
        }

    # Rural-specific certificate options
    elif step == "certidao_execucoes_fiscais_option":
        vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
        vendedores = session.get("vendedores", [])
        if vendedor_idx < len(vendedores):
            vendedor_name = vendedores[vendedor_idx].get("nome_completo", f"Vendedor {vendedor_idx + 1}")
        else:
            vendedor_name = f"Vendedor {vendedor_idx + 1}"
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Certidão de Execuções Fiscais para {vendedor_name}:",
            "options": ["Apresentar Certidão", "Usar Dispensa"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "certidao_distribuicao_acoes_option":
        vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
        vendedores = session.get("vendedores", [])
        if vendedor_idx < len(vendedores):
            vendedor_name = vendedores[vendedor_idx].get("nome_completo", f"Vendedor {vendedor_idx + 1}")
        else:
            vendedor_name = f"Vendedor {vendedor_idx + 1}"
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Certidão de Distribuição de Ações para {vendedor_name}:",
            "options": ["Apresentar Certidão", "Usar Dispensa"],
            "requires_file": False,
            "progress": progress
        }

    elif step == "certidao_ibama_option":
        vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
        vendedores = session.get("vendedores", [])
        if vendedor_idx < len(vendedores):
            vendedor_name = vendedores[vendedor_idx].get("nome_completo", f"Vendedor {vendedor_idx + 1}")
        else:
            vendedor_name = f"Vendedor {vendedor_idx + 1}"
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Certidão do IBAMA para {vendedor_name}:",
            "options": ["Apresentar Certidão", "Usar Dispensa"],
            "requires_file": False,
            "progress": progress
        }

    elif step.startswith("certidao_") and step.endswith("_option"):
        cert_name = session["temp_data"].get("cert_name", "Certidão")
        vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
        vendedores = session.get("vendedores", [])
        if vendedor_idx < len(vendedores):
            vendedor_name = vendedores[vendedor_idx].get("nome_completo", f"Vendedor {vendedor_idx + 1}")
        else:
            vendedor_name = f"Vendedor {vendedor_idx + 1}"
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"{cert_name} para {vendedor_name}:",
            "options": ["Apresentar Certidão", "Usar Dispensa"],
            "requires_file": False,
            "progress": progress
        }

    # Rural-specific certificate uploads
    elif step == "certidao_execucoes_fiscais_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Execuções Fiscais:",
            "requires_file": True,
            "file_description": "Certidão de Execuções Fiscais",
            "progress": progress
        }

    elif step == "certidao_distribuicao_acoes_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Distribuição de Ações:",
            "requires_file": True,
            "file_description": "Certidão de Distribuição de Ações",
            "progress": progress
        }

    elif step == "certidao_itr_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão do ITR:",
            "requires_file": True,
            "file_description": "Certidão do ITR - Imposto Territorial Rural",
            "progress": progress
        }

    elif step == "certidao_ccir_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload do CCIR 2025:",
            "requires_file": True,
            "file_description": "CCIR 2025 - Certificado de Cadastro de Imóvel Rural",
            "progress": progress
        }

    elif step == "certidao_ibama_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão do IBAMA:",
            "requires_file": True,
            "file_description": "Certidão do IBAMA",
            "progress": progress
        }

    # Conditional certificates for desmembramento
    elif step == "certidao_art_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da ART (Anotação de Responsabilidade Técnica):",
            "requires_file": True,
            "file_description": "ART - Anotação de Responsabilidade Técnica",
            "progress": progress
        }

    elif step == "certidao_planta_terreno_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Planta do Terreno:",
            "requires_file": True,
            "file_description": "Planta do Terreno com medidas e divisas",
            "progress": progress
        }

    elif step.startswith("certidao_") and step.endswith("_upload"):
        cert_name = session["temp_data"].get("cert_name", "Certidão")
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": f"Faça upload da {cert_name}:",
            "requires_file": True,
            "file_description": cert_name,
            "progress": progress
        }

    # Final data collection
    elif step == "valor_imovel":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Informe o valor do imóvel (ex: R$ 250.000,00):",
            "requires_file": False,
            "progress": "Finalizando..."
        }

    elif step == "forma_pagamento":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Forma de pagamento:",
            "options": ["À VISTA", "ANTERIORMENTE"],
            "requires_file": False,
            "progress": "Finalizando..."
        }

    elif step == "meio_pagamento":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Meio de pagamento:",
            "options": ["transferência bancária/pix", "dinheiro", "cheque"],
            "requires_file": False,
            "progress": "Finalizando..."
        }

    elif step == "condominio_option":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Certidão de Condomínio:",
            "options": ["Apresentar Certidão", "Usar Dispensa"],
            "requires_file": False,
            "progress": "Finalizando..."
        }

    elif step == "condominio_upload":
        return {
            "session_id": session["id"],
            "current_step": step,
            "question": "Faça upload da Certidão de Condomínio:",
            "requires_file": True,
            "file_description": "Certidão de Condomínio",
            "progress": "Finalizando..."
        }

    elif step == "processing":
        return {
            "session_id": session["id"],
            "current_step": step,
            "message": "Processando documentos e gerando escritura...",
            "requires_file": False,
            "progress": "Finalizando...",
            "auto_process": True
        }

    else:
        return {
            "session_id": session["id"],
            "current_step": "error",
            "question": "Erro: passo desconhecido",
            "requires_file": False,
            "progress": "Erro"
        }


def determine_next_step(session: Dict[str, Any], current_response: str = None) -> str:
    """Determine what the next step should be based on current state"""
    current = session["current_step"]

    # Increment step counter
    session["step_number"] = session.get("step_number", 1) + 1

    if current == "tipo_escritura":
        # Detect if this is a rural escritura
        if current_response == "Escritura Rural":
            session["is_rural"] = True
            session["tipo_escritura_rural"] = "rural"
        elif current_response == "Escritura Rural com Desmembramento de Área":
            session["is_rural"] = True
            session["tipo_escritura_rural"] = "rural_desmembramento"
        else:
            session["is_rural"] = False
        return "comprador_tipo"

    # Comprador flow
    elif current == "comprador_tipo":
        if current_response == "Pessoa Física":
            return "comprador_documento_tipo"
        else:
            return "comprador_empresa_upload"

    elif current == "comprador_documento_tipo":
        return "comprador_documento_upload"

    elif current == "comprador_documento_upload":
        return "comprador_casado"

    elif current == "comprador_casado":
        if current_response == "Sim":
            return "certidao_casamento_upload"
        else:
            return "mais_compradores"

    elif current == "certidao_casamento_upload":
        return "conjuge_assina"

    elif current == "conjuge_assina":
        if current_response == "Sim":
            return "conjuge_documento_tipo"
        else:
            return "mais_compradores"

    elif current == "conjuge_documento_tipo":
        return "conjuge_documento_upload"

    elif current == "conjuge_documento_upload":
        return "mais_compradores"

    elif current == "mais_compradores":
        if current_response == "Sim":
            return "comprador_tipo"
        else:
            return "vendedor_tipo"

    # Vendedor flow
    elif current == "vendedor_tipo":
        if current_response == "Pessoa Física":
            return "vendedor_documento_tipo"
        else:
            return "vendedor_empresa_upload"

    elif current == "vendedor_documento_tipo":
        return "vendedor_documento_upload"

    elif current == "vendedor_documento_upload":
        return "vendedor_casado"

    elif current == "vendedor_casado":
        if current_response == "Sim":
            return "vendedor_certidao_casamento_upload"
        else:
            return "mais_vendedores"

    elif current == "vendedor_certidao_casamento_upload":
        return "mais_vendedores"

    elif current == "mais_vendedores":
        if current_response == "Sim":
            return "vendedor_tipo"
        else:
            return "certidao_onus_upload"

    # Certidões flow
    elif current == "certidao_onus_upload":
        from workflow.certificates import get_next_certificate_step
        session["temp_data"]["vendedor_idx"] = 0
        session["temp_data"]["cert_type"] = "negativa_federal"
        session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
        return "certidao_negativa_federal_option"

    elif current.startswith("certidao_") and current.endswith("_option"):
        if current_response == "Usar Dispensa":
            from workflow.certificates import get_next_certificate_step
            return get_next_certificate_step(session)
        else:
            return current.replace("_option", "_upload")

    elif current.startswith("certidao_") and current.endswith("_upload"):
        from workflow.certificates import get_next_certificate_step
        return get_next_certificate_step(session)

    # Final steps
    elif current == "valor_imovel":
        return "forma_pagamento"

    elif current == "forma_pagamento":
        return "meio_pagamento"

    elif current == "meio_pagamento":
        return "processing"

    # Condominio steps
    elif current == "condominio_option":
        if current_response == "Usar Dispensa":
            return "valor_imovel"
        else:
            return "condominio_upload"

    elif current == "condominio_upload":
        return "valor_imovel"

    return "error"
