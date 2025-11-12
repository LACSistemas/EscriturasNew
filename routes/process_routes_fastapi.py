"""FastAPI Document processing routes"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any

from config import sessions
from services.ocr_service_async import extract_text_from_file_async
from services.ai_service_async import extract_data_with_gemini_async
from services.document_processor import process_all_documents, process_all_rural_documents
from workflow.steps import get_next_step, determine_next_step
from generators.escritura_generator import generate_escritura_text
from generators.escritura_rural_generator import generate_escritura_rural_text
from models.schemas import StepResponse, ProcessCompleteResponse

router = APIRouter(tags=["processing"])
logger = logging.getLogger(__name__)

# Client references
vision_client = None
gemini_model = None


def set_clients(vision, gemini):
    """Set the vision and gemini clients"""
    global vision_client, gemini_model
    vision_client = vision
    gemini_model = gemini


@router.post("/process")
async def process_document(
    request: Request,
    session_id: Optional[str] = Form(None),
    response: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Single endpoint that handles the entire document processing flow (async)"""

    try:
        logger.info(f"DEBUG: Process request received. session_id={session_id}, response={response}, file={file}")

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
            return get_next_step(sessions[session_id])

        # Validate session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        session = sessions[session_id]
        current_step = session["current_step"]

        # Handle processing step
        if current_step == "processing":
            try:
                # Get user_id from session
                user_id = request.session.get('user') if request.session.get('authenticated') else None

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
                return ProcessCompleteResponse(
                    session_id=session_id,
                    status="completed",
                    message="Escritura gerada com sucesso!",
                    extracted_data=result["extracted_data"],
                    escritura=result["escritura"],
                    all_extracted_data=result["extracted_data"]
                )
            except Exception as e:
                logger.error(f"ERROR: Processing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Erro ao processar documentos: {str(e)}")

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
                raise HTTPException(status_code=400, detail="Arquivo não fornecido")

            # Read file asynchronously
            content = await file.read()

            # Process with async OCR
            text = await extract_text_from_file_async(content, file.filename, vision_client)

            doc_type = session["temp_data"].get("documento_tipo")
            if doc_type == "Carteira de Identidade":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            elif doc_type == "CNH":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            else:  # Carteira de Trabalho
                prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

            # Extract with async AI
            extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

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

        # NOTE: This is simplified - full implementation would have 23+ step handlers
        # For production: implement all remaining handlers (same as Flask version)

        # Return the next step
        session["step_number"] = session.get("step_number", 1) + 1
        return get_next_step(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR: Exception in process_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
