"""Document processing routes"""
import uuid
import logging
from flask import Blueprint, request, jsonify, session as flask_session
from typing import Dict, Any

from config import sessions
from services.ocr_service import extract_text_from_file
from services.ai_service import extract_data_with_gemini
from services.document_processor import process_all_documents, process_all_rural_documents
from workflow.steps import get_next_step, determine_next_step
from workflow.certificates import get_next_certificate_step
from generators.escritura_generator import generate_escritura_text
from generators.escritura_rural_generator import generate_escritura_rural_text

process_bp = Blueprint('process', __name__)
logger = logging.getLogger(__name__)


# Import app-level dependencies
vision_client = None
gemini_model = None


def set_clients(vision, gemini):
    """Set the vision and gemini clients"""
    global vision_client, gemini_model
    vision_client = vision
    gemini_model = gemini


@process_bp.route('/process', methods=['POST'])
def process_document():
    """Single endpoint that handles the entire document processing flow"""

    try:
        logger.info(f"DEBUG: Process request received. Content-Type: {request.content_type}")
        logger.info(f"DEBUG: Form keys: {list(request.form.keys())}")
        logger.info(f"DEBUG: Files keys: {list(request.files.keys())}")

        # Get form data
        session_id = request.form.get('session_id')
        response = request.form.get('response')
        file = request.files.get('file')

        logger.info(f"DEBUG: session_id={session_id}, response={response}, file={file}")

        # Start new session if no session_id provided
        if not session_id:
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "id": session_id,
                "current_step": "tipo_escritura",
                "tipo_escritura": None,
                "compradores": [],
                "vendedores": [],
                "certidoes": {},
                "temp_data": {},
                "step_number": 1
            }
            return jsonify(get_next_step(sessions[session_id]))

        # Validate session exists
        if session_id not in sessions:
            return jsonify({"error": "Session not found or expired"}), 404

        session = sessions[session_id]
        current_step = session["current_step"]

        # Handle processing step
        if current_step == "processing":
            try:
                # Get user_id from Flask session
                user_id = flask_session.get('user') if flask_session.get('authenticated') else None

                # Check if this is a rural escritura and use appropriate template generator
                if session.get('is_rural'):
                    result = process_all_rural_documents(
                        session,
                        lambda s: generate_escritura_rural_text(s, user_id)
                    )
                else:
                    result = process_all_documents(
                        session,
                        lambda s: generate_escritura_text(s, user_id)
                    )
                # Clean up session
                del sessions[session_id]
                return jsonify({
                    "session_id": session_id,
                    "status": "completed",
                    "message": "Escritura gerada com sucesso!",
                    "extracted_data": result["extracted_data"],
                    "escritura": result["escritura"],
                    "all_extracted_data": result["extracted_data"]
                })
            except Exception as e:
                logger.error(f"ERROR: Processing failed: {str(e)}")
                return jsonify({
                    "session_id": session_id,
                    "status": "error",
                    "message": f"Erro ao processar documentos: {str(e)}"
                })

        # Process response based on current step
        if current_step == "tipo_escritura":
            session["tipo_escritura"] = response
            session["current_step"] = determine_next_step(session, response)

        elif current_step == "comprador_tipo":
            session["temp_data"]["tipo_pessoa"] = response
            session["current_step"] = determine_next_step(session, response)

        elif current_step == "comprador_documento_tipo":
            session["temp_data"]["documento_tipo"] = response
            session["current_step"] = determine_next_step(session, response)

        elif current_step == "comprador_documento_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400

            content = file.read()
            text = extract_text_from_file(content, file.filename, vision_client)

            doc_type = session["temp_data"].get("documento_tipo")
            if doc_type == "Carteira de Identidade":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            elif doc_type == "CNH":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            else:  # Carteira de Trabalho
                prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

            extracted = extract_data_with_gemini(text, prompt, gemini_model)

            # Store comprador data
            comprador = {
                "tipo": "Pessoa Física",
                "nome_completo": extracted.get("Nome Completo", ""),
                "data_nascimento": extracted.get("Data de Nascimento", ""),
                "documento_tipo": doc_type
            }

            if doc_type == "Carteira de Identidade":
                comprador["cpf"] = extracted.get("Número do CPF", "")
                comprador["sexo"] = extracted.get("Gênero", "")
            elif doc_type == "CNH":
                comprador["cnh_numero"] = extracted.get("Número da CNH", "")
                comprador["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
                comprador["sexo"] = extracted.get("Gênero", "")
            else:  # Carteira de Trabalho
                comprador["ctps_serie"] = extracted.get("Série da Carteira", "")
                comprador["ctps_numero"] = extracted.get("Número da Carteira", "")
                comprador["sexo"] = extracted.get("Gênero", "")

            session["temp_data"]["current_comprador"] = comprador
            session["current_step"] = determine_next_step(session, response)

        # NOTE: This is simplified - the full app.py has 23+ step handlers
        # For production, you'd need to implement all remaining handlers:
        # - comprador_empresa_upload
        # - comprador_casado
        # - certidao_casamento_upload
        # - conjuge_assina
        # - conjuge_documento_tipo
        # - conjuge_documento_upload
        # - mais_compradores
        # - vendedor_tipo/documento/casado/etc
        # - mais_vendedores
        # - certidao_onus_upload
        # - All certificate option/upload handlers
        # - valor_imovel, forma_pagamento, meio_pagamento
        # - condominio_option/upload

        # For now, return the next step
        session["step_number"] = session.get("step_number", 1) + 1
        return jsonify(get_next_step(session))

    except Exception as e:
        logger.error(f"ERROR: Exception in process_document: {str(e)}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
