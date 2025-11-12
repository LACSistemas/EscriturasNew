from flask import Flask, request, jsonify, session
from typing import List, Dict, Any
from enum import Enum
import json
from datetime import datetime
import os
from google.cloud import vision
import google.generativeai as genai
import uuid
from dotenv import load_dotenv
import sys
import logging
import fitz  # PyMuPDF

# Import our custom modules (now in root directory)
from database import (
    init_database, 
    get_cartorio_config, 
    update_cartorio_config,
    test_database_connection
)
from gender_concordance import (
    get_cartorio_template_data,
    build_escritura_header,
    build_escritura_authentication,
    build_escritura_declarations,
    build_escritura_final_clauses,
    validate_gender_concordance
)
from auth import authenticate_user, is_authenticated, get_current_user

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

load_dotenv() 

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
try:
    init_database()
    app.logger.info("Database initialized successfully")
except Exception as e:
    app.logger.error(f"Database initialization failed: {e}")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = app.logger
logger.setLevel(logging.DEBUG)

# Configure Google Cloud Vision (with error handling)
vision_client = None
try:
    vision_client = vision.ImageAnnotatorClient()
    app.logger.info("Google Cloud Vision client initialized successfully")
except Exception as e:
    app.logger.warning(f"Google Cloud Vision client failed to initialize: {e}")
    app.logger.warning("Vision OCR will not be available, but app will continue running")

# Configure Gemini
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        app.logger.info("Gemini AI client initialized successfully")
    else:
        gemini_model = None
        app.logger.warning("GEMINI_API_KEY not found in environment")
except Exception as e:
    gemini_model = None
    app.logger.warning(f"Gemini AI client failed to initialize: {e}")

# Enums
class TipoEscritura(str, Enum):
    LOTE = "Escritura de Lote"
    APTO = "Escritura de Apto"
    RURAL = "Escritura Rural"
    RURAL_DESMEMBRAMENTO = "Escritura Rural com Desmembramento de Área"

class TipoPessoa(str, Enum):
    FISICA = "Pessoa Física"
    JURIDICA = "Pessoa Jurídica"

class TipoDocumento(str, Enum):
    IDENTIDADE = "Carteira de Identidade"
    CNH = "CNH"
    CTPS = "Carteira de Trabalho"

class CertificateTypeRural(str, Enum):
    EXECUCOES_FISCAIS = "Certidão de Execuções Fiscais"
    DISTRIBUICAO_ACOES = "Certidão de Distribuição de Ações"
    ITR = "Certidão do ITR"
    CCIR = "CCIR 2025"
    IBAMA = "Certidão do IBAMA"
    ART = "ART"
    PLANTA_TERRENO = "Planta do Terreno"

# Session storage
sessions: Dict[str, Dict[str, Any]] = {}

# Helper functions
def extract_text_from_file(file_content: bytes, filename: str = "") -> str:
    """Process file content, handling both PDFs and images (based on working OLDAPP.py)"""
    try:
        # Determine if it's a PDF
        if filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF'):
            app.logger.info("DEBUG: Processing PDF file - converting to image first")
            # Convert PDF to image using PyMuPDF (like the working version)
            try:
                # Open PDF from bytes
                pdf_document = fitz.open(stream=file_content, filetype="pdf")
                
                if len(pdf_document) == 0:
                    raise Exception("No pages found in PDF")
                
                # Get first page
                page = pdf_document[0]
                
                # Convert page to image (PNG format)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Close the document
                pdf_document.close()
                
                app.logger.info("DEBUG: PDF converted to image, extracting text with Vision API")
                # Extract text from the converted image
                return extract_text_from_image(img_data)
            except Exception as e:
                app.logger.error(f"ERROR: Error processing PDF: {str(e)}")
                raise Exception(f"Error processing PDF: {str(e)}")
        else:
            app.logger.info("DEBUG: Processing as image directly")
            # Process as image directly
            return extract_text_from_image(file_content)
    except Exception as e:
        app.logger.error(f"ERROR: Exception in extract_text_from_file: {str(e)}")
        raise


def extract_text_from_image(image_content: bytes) -> str:
    """Extract text from image using Google Vision API (simplified like working version)"""
    if not vision_client:
        raise Exception("Google Cloud Vision client is not available. Check credentials configuration.")
    
    image = vision.Image(content=image_content)
    response = vision_client.text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")
    
    extracted_text = response.full_text_annotation.text if response.full_text_annotation else ""
    if not extracted_text:
        app.logger.warning("WARNING: Vision API extracted no text from image")
    else:
        app.logger.info(f"DEBUG: Vision API extracted {len(extracted_text)} characters")
    return extracted_text

def extract_data_with_gemini(text: str, prompt: str) -> Dict[str, Any]:
    """Use Gemini to extract structured data from text"""
    try:
        app.logger.info(f"DEBUG: Starting Gemini extraction. Text length: {len(text)}")
        full_prompt = f"""
        Analyze the following text and extract the requested information.
        Return ONLY a valid JSON object with the requested fields.
        
        Text to analyze:
        {text}
        
        Extract the following in JSON format:
        {prompt}
        
        Important: Return only the JSON object, no additional text or explanation.
        """
        
        if not gemini_model:
            raise Exception("Gemini AI client is not available. Check GEMINI_API_KEY configuration.")
        
        response = gemini_model.generate_content(full_prompt)
        app.logger.info(f"DEBUG: Gemini response received: {response.text[:100]}...")
        
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        
        result = json.loads(json_str.strip())
        app.logger.info(f"DEBUG: Gemini extraction successful: {result}")
        return result
    except json.JSONDecodeError as e:
        app.logger.error(f"ERROR: Failed to parse Gemini response as JSON: {e}")
        app.logger.error(f"ERROR: Gemini response was: {response.text}")
        raise Exception("Failed to parse Gemini response as JSON")
    except Exception as e:
        app.logger.error(f"ERROR: Exception in extract_data_with_gemini: {str(e)}")
        raise

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
        # Count includes current comprador being processed (like working version)
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
        # Count includes current vendedor being processed (like working version)
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
            "auto_process": True  # Signal frontend to auto-submit
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
        # This should not be reached since upload handling is done in process_document()
        # For urban, use the original logic
        session["temp_data"]["vendedor_idx"] = 0
        session["temp_data"]["cert_type"] = "negativa_federal"
        session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
        return "certidao_negativa_federal_option"
    
    elif current.startswith("certidao_") and current.endswith("_option"):
        if current_response == "Usar Dispensa":
            # This should not be reached since option handling is done in process_document()
            # Move to next certificate using urban flow as fallback
            return get_next_certificate_step(session)
        else:
            return current.replace("_option", "_upload")
    
    elif current.startswith("certidao_") and current.endswith("_upload"):
        # This should not be reached since upload handling is done in process_document()
        # Use urban flow as fallback
        return get_next_certificate_step(session)
    
    # Final steps
    elif current == "valor_imovel":
        return "forma_pagamento"
    
    elif current == "forma_pagamento":
        return "meio_pagamento"
    
    elif current == "meio_pagamento":
        return "processing"
    
    # Condominio steps (from working version)
    elif current == "condominio_option":
        if current_response == "Usar Dispensa":
            return "valor_imovel"
        else:
            return "condominio_upload"
    
    elif current == "condominio_upload":
        return "valor_imovel"
    
    return "error"

def get_next_certificate_step(session: Dict[str, Any]) -> str:
    """Determine next certificate to collect (based on working OLDAPP.py)"""
    # Route to rural certificate flow if this is a rural escritura
    if session.get("is_rural"):
        return get_next_rural_certificate_step(session)
    
    cert_order = [
        ("negativa_federal", "Certidão Negativa Federal"),
        ("debitos_tributarios", "Certidão de Débitos Tributários"),
        ("negativa_estadual", "Certidão Negativa Estadual"),
        ("debitos_trabalhistas", "Certidão de Débitos Trabalhistas"),
        ("indisponibilidade", "Certidão de Indisponibilidade de Bens")
    ]
    
    current_cert = session["temp_data"].get("cert_type")
    vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
    vendedores = session.get("vendedores", [])
    
    # Safety check (from working version)
    if not vendedores:
        return "valor_imovel"
    
    # Find current position
    current_pos = -1
    for i, (cert_type, _) in enumerate(cert_order):
        if cert_type == current_cert:
            current_pos = i
            break
    
    # Move to next certificate for current vendedor
    if current_pos < len(cert_order) - 1:
        next_cert, next_name = cert_order[current_pos + 1]
        session["temp_data"]["cert_type"] = next_cert
        session["temp_data"]["cert_name"] = next_name
        return f"certidao_{next_cert}_option"
    
    # Move to next vendedor if available
    elif vendedor_idx < len(vendedores) - 1:
        session["temp_data"]["vendedor_idx"] = vendedor_idx + 1
        session["temp_data"]["cert_type"] = "negativa_federal"
        session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
        return "certidao_negativa_federal_option"
    
    # All certificates collected for all vendedores
    else:
        # Check if we need to collect condominio declaration for Apto (from working version)
        if session.get("tipo_escritura") == "Escritura de Apto" and "condominio_processed" not in session["temp_data"]:
            session["temp_data"]["condominio_processed"] = True
            return "condominio_option"
        else:
            return "valor_imovel"

def get_next_rural_certificate_step(session: Dict[str, Any]) -> str:
    """Determine next certificate to collect for rural escrituras"""
    # Rural certificate order: PER-VENDOR ONLY (ônus is handled separately)
    cert_order = [
        # SHARED certificates (reuse existing urban extraction) - per vendor
        ("negativa_federal", "Certidão Negativa Federal"),
        ("debitos_tributarios", "Certidão de Débitos Tributários"),
        ("negativa_estadual", "Certidão Negativa Estadual"),
        ("debitos_trabalhistas", "Certidão de Débitos Trabalhistas"),
        ("indisponibilidade", "Certidão de Indisponibilidade de Bens"),
        # RURAL-ONLY certificates (new extraction needed) - per vendor
        ("execucoes_fiscais", "Certidão de Execuções Fiscais"),
        ("distribuicao_acoes", "Certidão de Distribuição de Ações"),
        ("ibama", "Certidão do IBAMA")
    ]
    
    # Property-level certificates (one for entire property)
    property_certs = [
        ("itr", "Certidão do ITR"),
        ("ccir", "CCIR 2025")
    ]
    
    current_cert = session["temp_data"].get("cert_type")
    vendedor_idx = session["temp_data"].get("vendedor_idx", 0)
    vendedores = session.get("vendedores", [])
    
    # Safety check
    if not vendedores:
        # Move to property certificates if no vendors processed yet
        if not session["temp_data"].get("property_certs_started"):
            session["temp_data"]["property_certs_started"] = True
            session["temp_data"]["cert_type"] = "itr"
            session["temp_data"]["cert_name"] = "Certidão do ITR"
            return "certidao_itr_upload"
        return "valor_imovel"
    
    # Handle Ônus first (only once, before per-vendor certificates)
    if not session["temp_data"].get("onus_processed"):
        if current_cert != "onus":
            session["temp_data"]["cert_type"] = "onus"
            session["temp_data"]["cert_name"] = "Certidão de Ônus"
            return "certidao_onus_upload"
        else:
            # Ônus processed, move to per-vendor certificates
            session["temp_data"]["onus_processed"] = True
            session["temp_data"]["cert_type"] = "negativa_federal"
            session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
            return "certidao_negativa_federal_option"
    
    # Check if we're in property certificate phase
    if session["temp_data"].get("property_certs_started"):
        # Handle property certificate progression
        if session["temp_data"]["cert_type"] == "itr":
            session["temp_data"]["cert_type"] = "ccir"
            session["temp_data"]["cert_name"] = "CCIR 2025"
            return "certidao_ccir_upload"
        elif session["temp_data"]["cert_type"] == "ccir":
            # Check if desmembramento requires ART and Planta
            if session.get("tipo_escritura_rural") == "rural_desmembramento":
                if not session["temp_data"].get("art_processed"):
                    session["temp_data"]["art_processed"] = True
                    session["temp_data"]["cert_type"] = "art"
                    session["temp_data"]["cert_name"] = "ART"
                    return "certidao_art_upload"
                elif not session["temp_data"].get("planta_processed"):
                    session["temp_data"]["planta_processed"] = True
                    session["temp_data"]["cert_type"] = "planta_terreno"
                    session["temp_data"]["cert_name"] = "Planta do Terreno"
                    return "certidao_planta_terreno_upload"
            # All certificates collected
            return "valor_imovel"
        else:
            # Unknown property certificate, finish
            return "valor_imovel"
    
    # Handle per-vendor certificates
    # Find current position in per-vendor certificates
    current_pos = -1
    for i, (cert_type, _) in enumerate(cert_order):
        if cert_type == current_cert:
            current_pos = i
            break
    
    # Move to next certificate for current vendedor
    if current_pos >= 0 and current_pos < len(cert_order) - 1:
        next_cert, next_name = cert_order[current_pos + 1]
        session["temp_data"]["cert_type"] = next_cert
        session["temp_data"]["cert_name"] = next_name
        return f"certidao_{next_cert}_option"
    
    # Move to next vendedor if available
    elif vendedor_idx < len(vendedores) - 1:
        session["temp_data"]["vendedor_idx"] = vendedor_idx + 1
        session["temp_data"]["cert_type"] = "negativa_federal"
        session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
        return "certidao_negativa_federal_option"
    
    # All per-vendor certificates collected, move to property certificates
    else:
        session["temp_data"]["property_certs_started"] = True
        session["temp_data"]["cert_type"] = "itr"
        session["temp_data"]["cert_name"] = "Certidão do ITR"
        return "certidao_itr_upload"

def format_date_for_deed() -> str:
    """Format today's date for the deed in Portuguese legal format (from working OLDAPP.py)"""
    today = datetime.now()
    
    # Number to words mapping
    day_words = {
        1: "primeiro", 2: "dois", 3: "três", 4: "quatro", 5: "cinco",
        6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
        11: "onze", 12: "doze", 13: "treze", 14: "quatorze", 15: "quinze",
        16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte",
        21: "vinte e um", 22: "vinte e dois", 23: "vinte e três", 24: "vinte e quatro",
        25: "vinte e cinco", 26: "vinte e seis", 27: "vinte e sete", 28: "vinte e oito",
        29: "vinte e nove", 30: "trinta", 31: "trinta e um"
    }
    
    month_names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    year_words = {
        2024: "dois mil e vinte e quatro",
        2025: "dois mil e vinte e cinco",
        2026: "dois mil e vinte e seis",
        2027: "dois mil e vinte e sete",
        2028: "dois mil e vinte e oito",
        2029: "dois mil e vinte e nove",
        2030: "dois mil e trinta"
    }
    
    day = today.day
    month = today.month
    year = today.year
    
    day_text = day_words.get(day, str(day))
    month_text = month_names.get(month, "")
    year_text = year_words.get(year, f"dois mil e {year - 2000}")
    
    return f"aos {day} ({day_text}) dias do mês de {month_text} do ano de {year} ({year_text})"

def ensure_temp_data_saved(session: Dict[str, Any]) -> None:
    """Ensure any remaining temp data gets moved to final arrays (from working OLDAPP.py)"""
    temp_data = session.get("temp_data", {})
    
    # Save current_comprador if exists
    if "current_comprador" in temp_data and temp_data["current_comprador"]:
        app.logger.info("DEBUG: Saving remaining current_comprador to final array")
        session["compradores"].append(temp_data["current_comprador"])
        temp_data["current_comprador"] = None
    
    # Save current_vendedor if exists  
    if "current_vendedor" in temp_data and temp_data["current_vendedor"]:
        app.logger.info("DEBUG: Saving remaining current_vendedor to final array")
        session["vendedores"].append(temp_data["current_vendedor"])
        temp_data["current_vendedor"] = None

def process_all_documents(session: Dict[str, Any]) -> Dict[str, Any]:
    """Process all collected documents and generate the deed (FIXED: Added missing ensure_temp_data_saved)"""
    app.logger.info("DEBUG: Processing final documents...")
    app.logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    app.logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    app.logger.info(f"DEBUG: temp_data = {session.get('temp_data', {})}")
    
    # CRITICAL FIX: Ensure any remaining temp data gets saved
    ensure_temp_data_saved(session)
    
    app.logger.info(f"DEBUG: After saving temp data:")
    app.logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    app.logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    
    all_data = {
        "tipo_escritura": session["tipo_escritura"],
        "compradores": session["compradores"],
        "vendedores": session["vendedores"],
        "certidoes": session["certidoes"],
        "valor": session.get("valor"),
        "forma_pagamento": session.get("forma_pagamento"),
        "meio_pagamento": session.get("meio_pagamento")
    }
    
    # Generate the escritura text
    escritura = generate_escritura_text(session)
    
    return {
        "extracted_data": all_data,
        "escritura": escritura
    }

def process_all_rural_documents(session: Dict[str, Any]) -> Dict[str, Any]:
    """Process all collected documents and generate the rural escritura using rural template"""
    app.logger.info("DEBUG: Processing final rural documents...")
    app.logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    app.logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    app.logger.info(f"DEBUG: rural type = {session.get('tipo_escritura_rural', 'unknown')}")
    app.logger.info(f"DEBUG: temp_data = {session.get('temp_data', {})}")
    
    # CRITICAL FIX: Ensure any remaining temp data gets saved
    ensure_temp_data_saved(session)
    
    app.logger.info(f"DEBUG: After saving temp data:")
    app.logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    app.logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    
    # Include rural-specific data in extracted data
    all_data = {
        "tipo_escritura": session["tipo_escritura"],
        "tipo_escritura_rural": session.get("tipo_escritura_rural"),
        "is_rural": session.get("is_rural", False),
        "compradores": session["compradores"],
        "vendedores": session["vendedores"],
        "certidoes": session["certidoes"],
        "valor": session.get("valor"),
        "forma_pagamento": session.get("forma_pagamento"),
        "meio_pagamento": session.get("meio_pagamento")
    }
    
    # Generate the rural escritura text using rural template generator
    escritura = generate_escritura_rural_text(session)
    
    return {
        "extracted_data": all_data,
        "escritura": escritura
    }

def generate_escritura_text(session: Dict[str, Any]) -> str:
    """Generate the final deed text with database-backed cartório configuration"""
    # Get authenticated user from Flask session for cartório configuration
    from flask import session as flask_session
    user_id = flask_session.get('user') if flask_session.get('authenticated') else None
    
    # Get cartório configuration from database
    cartorio_config = get_cartorio_config(user_id)
    if not cartorio_config:
        # Fallback to default if none found
        cartorio_config = {
            'distrito': 'Campo Grande / Jardim América',
            'municipio': 'Cariacica',
            'comarca': 'Vitória',
            'estado': 'Espírito Santo',
            'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
            'quem_assina': 'Tabeliã'
        }
    
    # Get template data with proper gender concordance
    template_data = get_cartorio_template_data(cartorio_config)
    
    # Determine gender suffixes for parties
    vendedor_suffixes = determine_gender_suffix(session["vendedores"], True)
    comprador_suffixes = determine_gender_suffix(session["compradores"], False)
    
    # Format parties
    vendedores_text = format_parties(session["vendedores"])
    compradores_text = format_parties(session["compradores"])
    
    # Build the deed text
    valor = session.get("valor", "***VALOR***")
    forma = session.get("forma_pagamento", "À VISTA")
    meio = session.get("meio_pagamento", "transferência bancária/pix")
    
    # Format the date (from working version)
    formatted_date = format_date_for_deed()
    
    # Build escritura header with proper gender concordance
    header = build_escritura_header(template_data, formatted_date)
    
    # Build authentication section with proper gender concordance  
    auth_section = build_escritura_authentication(template_data)
    
    # Combine header with parties information
    escritura = f"""{header} de um lado como **{vendedor_suffixes['title']}**: {vendedores_text}; e de outro lado, como **{comprador_suffixes['title']}**: {compradores_text}; {auth_section}"""
    
    # Get property information from Certidão de Ônus (CRITICAL FIX: Using correct field names)
    onus_data = session.get("certidoes", {}).get("onus", {})
    imovel_descricao = onus_data.get("Descrição breve do imóvel", "***IMOVEL***")
    oficio_numero = onus_data.get("Número do Ofício (apenas o número, ex: 1, 2, 3)", "***")
    zona_cartorio = onus_data.get("Zona do Cartório (ex: 1ª Zona, 2ª Zona)", "***")
    cidade_cartorio = onus_data.get("Cidade do Cartório", "***")
    matricula_numero = onus_data.get("Número da Matrícula do Registro", "***")
    livro_numero = onus_data.get("Número do Livro", "***")

    # Add property description and sale terms
    escritura += f""" E pel{vendedor_suffixes['article']} **{vendedor_suffixes['title']}** referid{vendedor_suffixes['article']}, foi dito que {'são' if len(session['vendedores']) > 1 else 'é'} don{vendedor_suffixes['article']}, senhor{'es' if len(session['vendedores']) > 1 else ''} e legítim{vendedor_suffixes['article']} possuid{vendedor_suffixes['possessive']}, absolutamente livre e desembaraçado de todo e qualquer ônus real, do imóvel constituído pelo: {imovel_descricao}; devidamente registrado no Cartório de Registro Geral de Imóveis do {oficio_numero}º Ofício - {zona_cartorio} - {cidade_cartorio}, matricula nº {matricula_numero} do livro nº {livro_numero}, com valor venal atribuído pela municipalidade local de ********; que assim possuindo o referido imóvel, vende ao **{comprador_suffixes['title']}**, como efetivamente vendido tem, por bem desta escritura, da cláusula CONSTITUTI, e na melhor forma de direito, pelo preço certo e ajustado de **[{valor}]**, pago **[{forma}]** em moeda corrente nacional através de ***{meio}***, do que desde já, lhes dá plena, rasa e geral quitação da importância recebida, para nada mais exigirem com relação a presente venda, transmitindo, como de fato ora transmite na pessoa d{comprador_suffixes['article']} **{comprador_suffixes['title']}**, todo direito, posse, domínio e ação que exerciam sobre o referido imovel, e prometendo por si e seus sucessores legítimos a presente venda, boa, firme e valiosa para sempre, obrigando-se a responderem pela evicção de direito, se chamado a autoria. Pel{comprador_suffixes['article']} **{comprador_suffixes['title']}**, me foi dito que, aceita a presente escritura como nela se contem e declara, por estar o mesmo de inteiro com o ajustado e contratado entre si e {vendedor_suffixes['article']} **{vendedor_suffixes['title']}**. Foram apresentados as seguintes certidões e foram feitas as seguintes declarações:"""
    
    # Add certificates section
    escritura += format_certificates_section(session)
    
    # Add declarations with proper gender concordance
    declarations = build_escritura_declarations(template_data)
    final_clauses = build_escritura_final_clauses(template_data)
    
    escritura += f"""

**13º)** Declarações: **D{comprador_suffixes['article'].upper()} {comprador_suffixes['title']}:**

a.1) Concorda com os termos desta escritura;

{declarations}

a.3) Que esta ciente, assim, nos termos do item anterior, que caso o imóvel seja avaliado pela municipalidade em valor superior ao declarado, será necessário promover o aditamento da presente Escritura e realizar a devida complementação de emolumentos.

**b) D{vendedor_suffixes['article'].upper()} {vendedor_suffixes['title']}:**

b.1) Sob responsabilidade civil e penal, que sobre o imóvel objeto da presente escritura não incide nenhuma ação ou pendência judicial ou extrajudicial, nem ações reais e pessoais reipersecutórias e nem outros ônus reais;

b.2) Não existir débitos condominiais, ordinários e extraordinários, referente aos imóveis objetos da presente escritura pública. De acordo com o artigo 649, parágrafo único do Código de Normas da Egrégia Corregedoria Geral de Justiça do Estado do Espírito Santo, as partes foram orientadas "que a ausência da referida prova não isenta os responsáveis, de acordo com a lei civil, ao pagamento do débito condominial, dando ciência e fazendo constar expressamente da escritura que o adquirente, mesmo ciente de que passa a responder pelos débitos do alienante, em relação ao condomínio, inclusive multa e juros (CC art. 1.345), dispensou a apresentação da prova de quitação das obrigações de que trata o caput deste artigo", qual seja, os débitos condominiais;

{final_clauses}

c.2) Concordam com todos os termos e condições acima mencionados, e a pedido delas, lavro a escritura em meu livro de notas;

c.3) Que para fins de cumprimento do provimento do CNJ nº 88/2019, não são pessoas politicamente expostas e, nem são parentes de até 1º grau de pessoas politicamente expostas, bem como, não são estreitos colaboradores de pessoas politicamente expostas;

c.4) As partes requerem ao Oficial de Registro de Imóveis competente, que promova na matrícula antes mencionada, todos e quaisquer atos de registros e de averbações que se fizerem necessárias para o fiel cumprimento do registro desta escritura, junto ao Registro de Imóveis competente.

c.5) As partes envolvidas neste ato foram cientificadas da possibilidade de obtenção da Certidão Negativa de Débitos Trabalhistas (CNDT), nos termos do artigo 642-A do CLT; A DOI referente ao presente instrumento será emitida regularmente e enviada à SRF, no prazo estabelecido pela IN n.° 1.112 RFB de 28/12/2010.

c.6) Todas as partes foram informadas por esta serventia da proibição e ilegalidade de concessão de descontos ou comissões na cobrança dos emolumentos, nos termos dos artigos 6º, inciso XVIII e 7º, incisos III e IV do Provimento da CGJ/ES nº 07/2024 (Código de ética e de conduta dos responsáveis pelas serventias extrajudiciais do Estado do Espírito Santo), sem prejuízo da apuração de condutas que constituam falta disciplinar, nos termos da lei e dos regulamentos da Corregedoria Geral da Justiça, ficando ressalvadas as hipóteses legais"."""
    
    return escritura

def generate_escritura_rural_text(session: Dict[str, Any]) -> str:
    """Generate the final rural escritura text following templaterural.md specifications"""
    # Get authenticated user from Flask session for cartório configuration
    from flask import session as flask_session
    user_id = flask_session.get('user') if flask_session.get('authenticated') else None
    
    # Get cartório configuration from database
    cartorio_config = get_cartorio_config(user_id)
    if not cartorio_config:
        # Fallback to default if none found
        cartorio_config = {
            'distrito': 'Campo Grande / Jardim América',
            'municipio': 'Cariacica',
            'comarca': 'Vitória',
            'estado': 'Espírito Santo',
            'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
            'quem_assina': 'Tabeliã'
        }
    
    # Get template data with proper gender concordance
    template_data = get_cartorio_template_data(cartorio_config)
    
    # Apply defaults to parties before formatting (CRITICAL: Rural needs defaults for missing fields)
    rural_compradores = []
    for comprador in session["compradores"]:
        rural_comprador = comprador.copy()
        # Add defaults for missing rural fields
        if rural_comprador.get('tipo') == 'Pessoa Física':
            # Set profession based on gender
            if rural_comprador.get('sexo', '').lower() in ['feminino', 'f', 'female']:
                rural_comprador.setdefault('profissao', 'lavradora')
            else:
                rural_comprador.setdefault('profissao', 'produtor rural')
            
            # Set default location and family
            rural_comprador.setdefault('naturalidade', 'Cariacica')
            rural_comprador.setdefault('pai_nome', 'PAI_NOME_COMPLETO')
            rural_comprador.setdefault('mae_nome', 'MAE_NOME_COMPLETO')
            rural_comprador.setdefault('endereco', 'Endereço completo, Cidade-ES')
        rural_compradores.append(rural_comprador)
    
    rural_vendedores = []
    for vendedor in session["vendedores"]:
        rural_vendedor = vendedor.copy()
        # Add defaults for missing rural fields
        if rural_vendedor.get('tipo') == 'Pessoa Física':
            # Set profession based on gender
            if rural_vendedor.get('sexo', '').lower() in ['feminino', 'f', 'female']:
                rural_vendedor.setdefault('profissao', 'lavradora')
            else:
                rural_vendedor.setdefault('profissao', 'produtor rural')
            
            # Set default location and family
            rural_vendedor.setdefault('naturalidade', 'Cariacica')
            rural_vendedor.setdefault('pai_nome', 'PAI_NOME_COMPLETO')
            rural_vendedor.setdefault('mae_nome', 'MAE_NOME_COMPLETO')
            rural_vendedor.setdefault('endereco', 'Endereço completo, Cidade-ES')
        rural_vendedores.append(rural_vendedor)
    
    # Build rural header with OUTORGANTE/OUTORGADO terminology
    header = build_rural_header(session)
    
    # Format the date
    formatted_date = format_date_for_deed()
    
    # Build SAIBAM section with cartório info
    saibam_section = f"""S A I B A M quantos esta pública escritura de COMPRA E VENDA bastante virem que aos {formatted_date}, às 10:00 horas, em meu Cartório, sito à {template_data['endereco']}, perante mim {template_data['quem_assina']}, compareceram partes entre sí, justas e convencionadas, a saber,"""
    
    # Format parties with rural formatting (includes defaults)
    vendedores_text = format_rural_parties(rural_vendedores, True)
    compradores_text = format_rural_parties(rural_compradores, False)
    
    # Authentication line
    auth_line = f"Sendo as presentes pessoas reconhecidas como as próprias de que trato por mim {template_data['quem_assina']}, de cuja identidade e capacidade jurídica, DOU FÉ."
    
    # Property description (uses extended Ônus data)
    if session.get("tipo_escritura_rural") == "rural_desmembramento":
        property_description = build_rural_desmembramento_description(session)
    else:
        property_description = build_rural_property_description(session)
    
    # Payment terms
    valor = session.get("valor", "R$ 100.000,00")
    forma = session.get("forma_pagamento", "À vista")
    meio = session.get("meio_pagamento", "transferência bancária")
    
    payment_section = f"""1.2 - e achando-se contratado, com os Outorgados Compradores, por bem desta escritura, e na melhor forma de direito para lhe vender, como de fato vendido tem o imóvel descrito pelo preço certo e ajustado de direito por {valor} ({spell_out_currency(valor)}), pago em espécie na data de hoje, aqui; importância essa que o Outorgante Vendedor confessa e declara haver recebido em moeda corrente, pelo que se dá por pago e satisfeito, e por isso dá plena, geral e irrevogável quitação deste pagamento para nunca mais o repetirem, desde já transferindo-lhes toda a posse, domínio, direito e ação que exercia sobre o imóvel ora vendido, respondendo pela evicção de direito, quando chamados à autoria."""
    
    # General dispositions with rural-specific clauses
    general_dispositions = """2. - DAS DISPOSIÇÕES GERAIS: 2.1 - Os comparecentes declaram que: a) sob responsabilidade civil e criminal que os fatos aqui relatados e declarações feitas são exata expressão da verdade; b) foram informados que qualquer pessoa pode ter acesso às informações aqui prestadas; c) estão cientes de que esta pública escritura deverá ser registrada no Registro de Imóveis competente; d) fazem a manifestação da vontade nesta escritura sempre boa, firme e valiosa, afirmando que são verdadeiras e isentas de vícios.

2.13- As partes declaram que têm conhecimento da necessidade de se apresentar o CAR (Cadastro Ambiental Rural) no ato do registro de imóveis.

2.14 - As partes declaram que têm conhecimento de que a partir de 20 de novembro de 2025, será necessário apresentar o georreferenciamento certificado pelo INCRA."""
    
    # Certificates section (handles both shared and rural-only certificates)
    certificates_section = format_rural_certificates_section(session)
    
    # Final declarations
    final_declarations = f"""4 - DAS NOTAS EXPLICATIVAS: 4.1 - As partes estão cientes de que a cobrança dos emolumentos da presente Escritura Pública está de acordo com a Lei Estadual nº 3.151/78.

Foi emitida a Declaração sobre a Operação Imobiliária (DOI) conforme IN/RFB nº 1.112/10.

Declara o Outorgante Vendedor, que para fins de direito, não é contribuinte obrigatório do INSS.

Declaram os Outorgados Compradores, sob pena da Lei, que o imóvel da presente transação não será utilizado como depósito de agrotóxicos, radioativos ou que venha a produzir poluição ambiental de qualquer natureza.

ASSIM O DISSERAM do que dou fé e me pediram este instrumento que lhes li, aceitaram e assinam, {formatted_date}"""
    
    # Combine all sections
    escritura = f"""{header}

{saibam_section}

{vendedores_text}

{compradores_text}

{auth_line}

{property_description}

{payment_section}

{general_dispositions}

{certificates_section}

{final_declarations}"""
    
    return escritura

def format_rural_parties(parties: List[Dict], is_vendedor: bool) -> str:
    """Format party information for rural escrituras following Section 3 of templaterural.md"""
    if not parties:
        return "***PARTIES NOT FOUND***"
    
    formatted_parties = []
    
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            # Get gender agreement for proper honorifics
            gender_agreement = get_gender_agreement(party)
            gender = party.get("sexo", "").lower()
            honorific = "a Sra." if gender in ['feminino', 'f', 'female'] else "o Sr."
            
            # Format name in uppercase
            nome_completo = party.get("nome_completo", "NOME_COMPLETO").upper()
            
            # Format birth date
            data_nascimento = format_birth_date(party.get("data_nascimento", "01/01/1980"))
            
            # Marital status with proper formatting
            casado = party.get("casado", False)
            if casado:
                regime_bens = party.get("regime_bens", "Comunhão parcial de bens")
                # Format marriage date if available
                marriage_info = f"casado sob o Regime da {regime_bens}"
                if party.get("data_casamento"):
                    marriage_date = format_marriage_date(party.get("data_casamento"))
                    marriage_info = f"casado aos {marriage_date}, sob o Regime da {regime_bens}"
                marital_status = marriage_info
            else:
                marital_status = "solteiro, não possui união estável"
            
            # Profession (with defaults applied)
            profissao = party.get("profissao", "produtor rural")
            
            # Document information with proper formatting
            documento_tipo = party.get("documento_tipo", "Carteira de Identidade")
            if documento_tipo == "Carteira de Identidade":
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da carteira de identidade e inscrito no CPF/MF sob o nº {cpf}"
            elif documento_tipo == "CNH":
                cnh_numero = party.get("cnh_numero", "00000000000")
                cnh_orgao = party.get("cnh_orgao_expedidor", "DETRAN/ES")
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da CNH nº {cnh_numero} expedida pelo {cnh_orgao} e inscrito no CPF/MF sob o nº {cpf}"
            else:  # CTPS
                ctps_numero = party.get("ctps_numero", "0000000")
                ctps_serie = party.get("ctps_serie", "0000")
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da CTPS nº {ctps_numero} série {ctps_serie}-ES e inscrito no CPF/MF sob o nº {cpf}"
            
            # Birth place and parents (with defaults)
            naturalidade = party.get("naturalidade", "Cariacica")
            pai_nome = party.get("pai_nome", "PAI_NOME_COMPLETO")
            mae_nome = party.get("mae_nome", "MAE_NOME_COMPLETO")
            
            # Address (with defaults)
            endereco = party.get("endereco", "Endereço completo, Cidade-ES")
            
            # Build the party text according to Section 3 format
            party_prefix = "de um lado, como Outorgante Vendedor:" if is_vendedor else "e de outro lado na qualidade de Outorgado Comprador:"
            
            party_text = f"{party_prefix} {honorific} {nome_completo}, {gender_agreement['nascido']} aos {data_nascimento}, brasileiro, {marital_status}, {profissao}, {doc_text}, natural de {naturalidade}-ES, filho de {pai_nome} e de {mae_nome}, residente e domiciliado {endereco}"
            
            # Add spouse information if they sign
            if casado and party.get("conjuge_assina") and party.get("conjuge_data"):
                conj = party["conjuge_data"]
                conj_gender_agreement = get_gender_agreement(conj)
                conj_gender = conj.get("sexo", "").lower()
                conj_honorific = "sua esposa" if conj_gender in ['feminino', 'f', 'female'] else "seu esposo"
                conj_sra_sr = "a Sra." if conj_gender in ['feminino', 'f', 'female'] else "o Sr."
                conj_nome = conj.get("nome_completo", "CONJUGE_NOME").upper()
                conj_nascimento = format_birth_date(conj.get("data_nascimento", "01/01/1980"))
                conj_profissao = conj.get("profissao", "lavradora" if conj_gender in ['feminino', 'f', 'female'] else "produtor rural")
                
                # Spouse document formatting
                conj_doc_tipo = conj.get("documento_tipo", "Carteira de Identidade")
                if conj_doc_tipo == "Carteira de Identidade":
                    conj_cpf = conj.get("cpf", "000.000.000-00")
                    conj_doc_text = f"portadora da carteira de identidade e inscrita no CPF/MF sob o nº {conj_cpf}" if conj_gender in ['feminino', 'f', 'female'] else f"portador da carteira de identidade e inscrito no CPF/MF sob o nº {conj_cpf}"
                elif conj_doc_tipo == "CNH":
                    conj_cnh_numero = conj.get("cnh_numero", "00000000000")
                    conj_cnh_orgao = conj.get("cnh_orgao_expedidor", "DETRAN/ES")
                    conj_cpf = conj.get("cpf", "000.000.000-00")
                    portador_word = "portadora" if conj_gender in ['feminino', 'f', 'female'] else "portador"
                    inscrito_word = "inscrita" if conj_gender in ['feminino', 'f', 'female'] else "inscrito"
                    conj_doc_text = f"{portador_word} da CNH nº {conj_cnh_numero} expedida pelo {conj_cnh_orgao} e {inscrito_word} no CPF/MF sob o nº {conj_cpf}"
                else:  # CTPS
                    conj_ctps_numero = conj.get("ctps_numero", "0000000")
                    conj_ctps_serie = conj.get("ctps_serie", "0000")
                    conj_cpf = conj.get("cpf", "000.000.000-00")
                    portador_word = "portadora" if conj_gender in ['feminino', 'f', 'female'] else "portador"
                    inscrito_word = "inscrita" if conj_gender in ['feminino', 'f', 'female'] else "inscrito"
                    conj_doc_text = f"{portador_word} da CTPS nº {conj_ctps_numero} série {conj_ctps_serie}-ES e {inscrito_word} no CPF/MF sob o nº {conj_cpf}"
                
                conj_naturalidade = conj.get("naturalidade", "Cariacica")
                conj_pai = conj.get("pai_nome", "PAI_CONJUGE_NOME")
                conj_mae = conj.get("mae_nome", "MAE_CONJUGE_NOME")
                
                party_text += f", e {conj_honorific}, {conj_sra_sr} {conj_nome}, {conj_gender_agreement['nascido']} aos {conj_nascimento}, brasileira, {conj_profissao}, {conj_doc_text}, natural de {conj_naturalidade}-ES, filha de {conj_pai} e de {conj_mae}, ambos residentes e domiciliados {endereco}"
            
            formatted_parties.append(party_text)
            
        else:  # Pessoa Jurídica
            razao_social = party.get("razao_social", "EMPRESA NOME").upper()
            cnpj = party.get("cnpj", "00.000.000/0000-00")
            endereco_empresa = party.get("endereco", "Endereço da empresa, Cidade-ES")
            
            # For companies, we need representative information (would need to be collected)
            representative_name = "REPRESENTANTE NOME"
            representative_cpf = "000.000.000-00"
            representative_address = endereco_empresa
            
            party_prefix = "de um lado, como Outorgante Vendedor:" if is_vendedor else "e de outro lado na qualidade de Outorgado Comprador:"
            
            party_text = f"{party_prefix} {razao_social}, pessoa jurídica de direito privado, inscrita no CNPJ/MF sob o nº {cnpj}, com sede em {endereco_empresa}, neste ato representada por {representative_name}, brasileiro, casado, empresário, inscrito no CPF/MF sob o nº {representative_cpf}, residente e domiciliado {representative_address}"
            
            formatted_parties.append(party_text)
    
    return ";\n\n".join(formatted_parties)

def build_rural_property_description(session: Dict[str, Any]) -> str:
    """Build standard rural property description following Section 5.1 of templaterural.md"""
    # Get extended Ônus data (rural has additional fields)
    onus = session.get('certidoes', {}).get('onus', {})
    
    # Rural-specific fields from extended extraction
    location = onus.get('Localização do imóvel rural', 'LOCALIZAÇÃO')
    city = onus.get('Município do imóvel', 'MUNICÍPIO')
    area_total = onus.get('Área total em m²', '0')
    north_owner = onus.get('Nome do proprietário ao Norte', 'N/A')
    south_owner = onus.get('Nome do proprietário ao Sul', 'N/A')
    east_owner = onus.get('Nome do proprietário ao Leste', 'N/A')
    west_owner = onus.get('Nome do proprietário ao Oeste', 'N/A')
    property_name = onus.get('Nome da propriedade (ex: Sítio da Vitória)', 'PROPRIEDADE')
    
    # Standard Ônus fields
    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    registration_number = onus.get('Número da Matrícula do Registro', 'MATRÍCULA')
    book_number = onus.get('Número do Livro', 'LIVRO')
    
    # Get property certificates data
    itr = session.get('certidoes', {}).get('itr', {})
    ccir = session.get('certidoes', {}).get('ccir', {})
    
    cib_number = itr.get('Numero do CIB', 'CIB_NUMBER')
    ccir_number = ccir.get('Numero do Certificado', 'CCIR_NUMBER')
    
    # Convert area to written format
    area_written = spell_out_area(area_total)
    
    # Build property description following Section 5.1 template
    property_description = f"""1- DA COMPRA E VENDA: E, perante mim [QUEM_ASSINA], pelo Outorgante Vendedor me foi dito que é senhor, legítimo possuidor e vende o imóvel seguinte: 1.1- Um terreno rural, situado em {location}, Município de {city}-ES, medindo a área total de {area_total} m² ({area_written}), confrontando-se ao Norte com imóvel pertencente a {north_owner}, ao Sul com imóvel pertencente a {south_owner}, a Leste com imóveis pertencentes a {east_owner}, e ao Oeste com imóvel pertencente a {west_owner}. Imóvel este cadastrado no INCRA sob o nº {cib_number}, módulo fiscal de [FISCAL_MODULE] ha, nº módulos fiscais de [NUM_MODULES], e a Fração Mínima de Parcelamento (FMP) de [FMP] ha; inscrito na Receita Federal sob o CIB nº {cib_number}, sob a denominação de "{property_name}". Matriculado no Cartório do {office_number}º Ofício da Comarca de [COMARCA]-ES sob a matrícula nº {registration_number}, pág [PAGE] do Livro nº {book_number};"""
    
    return property_description

def build_rural_desmembramento_description(session: Dict[str, Any]) -> str:
    """Build rural property description with desmembramento following Section 5.2 of templaterural.md"""
    # Get extended Ônus data
    onus = session.get('certidoes', {}).get('onus', {})
    
    # Rural-specific fields from extended extraction
    location = onus.get('Localização do imóvel rural', 'LOCALIZAÇÃO')
    city = onus.get('Município do imóvel', 'MUNICÍPIO')
    original_area = onus.get('Área total em m²', '0')
    north_owner = onus.get('Nome do proprietário ao Norte', 'N/A')
    south_owner = onus.get('Nome do proprietário ao Sul', 'N/A')
    east_owner = onus.get('Nome do proprietário ao Leste', 'N/A')
    west_owner = onus.get('Nome do proprietário ao Oeste', 'N/A')
    property_name = onus.get('Nome da propriedade (ex: Sítio da Vitória)', 'PROPRIEDADE')
    
    # Standard Ônus fields
    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    registration_number = onus.get('Número da Matrícula do Registro', 'MATRÍCULA')
    book_number = onus.get('Número do Livro', 'LIVRO')
    
    # Get desmembramento data from Planta certificate
    planta = session.get('certidoes', {}).get('planta_terreno', {})
    subdivided_area = planta.get('Área do Terreno (Numero e Por Extenso)', '0')
    perimeter = planta.get('Perimetro do Terreno (numero e por extenso)', '0')
    planta_north = planta.get('Nome do Proprietario do Terreno ao Norte (Se nenhum, N/A)', north_owner)
    planta_south = planta.get('Nome do Proprietario do Terreno ao Sul (Se nenhum, N/A)', south_owner)
    planta_east = planta.get('Nome do Proprietario do Terreno ao Leste (Se nenhum, N/A)', east_owner)
    planta_west = planta.get('Nome do Proprietario do Terreno ao Oeste (Se nenhum, N/A)', west_owner)
    
    # Get technical data from ART certificate
    art = session.get('certidoes', {}).get('art', {})
    technician_title = art.get('Titulo Profissional do Tecnico', 'Engenheiro Agrônomo')
    technician_name = art.get('Nome do Tecnico', 'TÉCNICO RESPONSÁVEL')
    cfta_registration = art.get('Registro CFTA do Tecnico', 'CFTA_REG')
    trt_number = art.get('Numero do TRT', 'TRT_NUMBER')
    
    # Get property certificates data
    itr = session.get('certidoes', {}).get('itr', {})
    cib_number = itr.get('Numero do CIB', 'CIB_NUMBER')
    
    # Calculate remaining area
    try:
        original_area_num = float(original_area.replace(',', '.')) if isinstance(original_area, str) else float(original_area)
        subdivided_area_parts = subdivided_area.split(' ') if isinstance(subdivided_area, str) else [str(subdivided_area)]
        subdivided_area_num = float(subdivided_area_parts[0].replace(',', '.'))
        remaining_area_num = original_area_num - subdivided_area_num
        remaining_area = str(int(remaining_area_num)) if remaining_area_num == int(remaining_area_num) else str(remaining_area_num)
    except:
        remaining_area = "ÁREA_REMANESCENTE"
    
    # Convert areas to written format
    area_written = spell_out_area(subdivided_area.split(' ')[0] if isinstance(subdivided_area, str) else str(subdivided_area))
    original_area_written = spell_out_area(original_area)
    remaining_area_written = spell_out_area(remaining_area)
    perimeter_written = spell_out_area(perimeter.split(' ')[0] if isinstance(perimeter, str) else str(perimeter))
    
    # Build desmembramento description following Section 5.2 template
    property_description = f"""1- DA COMPRA E VENDA: E, perante mim [QUEM_ASSINA], pelo Outorgante Vendedor me foi dito que é senhor, legítimo possuidor e vende o imóvel seguinte: 1.1- Um terreno rural e legitimado, situado em {location}, Município de {city}-ES, medindo a área de {subdivided_area} m² ({area_written}) e perímetro de {perimeter} m ({perimeter_written}), confrontando-se ao Norte com imóvel pertencente a {planta_north}, ao Sul com imóvel pertencente a {planta_south}, a Leste com imóveis pertencentes a {planta_east}, e a Oeste com imóvel pertencente a {planta_west}; descrito topograficamente e caracterizado na planta e no memorial descritivo, realizados pelo {technician_title}, o Sr. {technician_name}, Registro CFTA: {cfta_registration}, planta datada de [PLAN_DATE], com Termo de Responsabilidade Técnica (TRT) sob o nº {trt_number}. Imóvel este que será desmembrado do terreno original, medindo a área total de {original_area} m² ({original_area_written}), confrontando-se ao Norte com imóvel pertencente a {north_owner}, ao Sul com imóvel pertencente a {south_owner}, a Leste com imóveis pertencentes a {east_owner} e ao Oeste com imóveis pertencentes a {west_owner}. Imóvel este cadastrado no INCRA sob o nº {cib_number}, módulo fiscal de [FISCAL_MODULE] ha, nº módulos fiscais de [NUM_MODULES], e a Fração Mínima de Parcelamento (FMP) de [FMP] ha; inscrito na Receita Federal sob o CIB nº {cib_number}, sob a denominação de "{property_name}". Matriculado no Cartório do {office_number}º Ofício da Comarca de [COMARCA]-ES sob a matrícula nº {registration_number}, pág [PAGE] do Livro nº {book_number}; 1.1.1 - restando para o Outorgante Vendedor a área remanescente total de {remaining_area} m² ({remaining_area_written}), confrontando-se por seus diversos lados com quem de direito."""
    
    return property_description

def build_rural_header(session: Dict[str, Any]) -> str:
    """Build the escritura header following Section 1 of templaterural.md with OUTORGANTE/OUTORGADO terminology"""
    vendedores = session.get("vendedores", [])
    compradores = session.get("compradores", [])
    
    # Extract party names for header
    vendedor_names = extract_party_names(vendedores, "vendedor")
    comprador_names = extract_party_names(compradores, "comprador")
    
    # Determine singular/plural for vendors
    if len(vendedores) == 1:
        vendedor_title = "OUTORGANTE VENDEDOR"
    else:
        vendedor_title = "OUTORGANTES VENDEDORES"
    
    # Determine singular/plural for buyers
    if len(compradores) == 1:
        comprador_title = "OUTORGADO COMPRADOR"
    else:
        comprador_title = "OUTORGADOS COMPRADORES"
    
    # Build header following Section 1 template
    header = f"""ESCRITURA PÚBLICA DE COMPRA E VENDA QUE FAZ COMO {vendedor_title} {vendedor_names}, E COMO {comprador_title} {comprador_names}, NA FORMA ABAIXO:"""
    
    return header

def extract_party_names(parties: List[Dict], party_type: str) -> str:
    """Extract names for header with 'E' conjunction for multiple parties"""
    if not parties:
        return "***NAMES NOT FOUND***"
    
    names = []
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            nome = party.get("nome_completo", "NOME_COMPLETO").upper()
            names.append(nome)
        else:  # Pessoa Jurídica
            razao_social = party.get("razao_social", "EMPRESA_NOME").upper()
            names.append(razao_social)
    
    # Join names with 'E' for the last item
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} E {names[1]}"
    else:
        return ", ".join(names[:-1]) + f" E {names[-1]}"

def format_rural_certificates_section(session: Dict[str, Any]) -> str:
    """Format rural certificates section following Section 8 of templaterural.md"""
    certificates = []
    cert_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
    cert_index = 0
    
    # Header
    certificates.append("3 - Foram-me apresentadas e ficam arquivadas as seguintes CERTIDÕES E DOCUMENTOS:")
    
    # A) Certidão de Ônus (always first for rural)
    onus = session.get('certidoes', {}).get('onus', {})
    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    city = onus.get('Cidade do Cartório', 'CIDADE')
    onus_date = onus.get('Data de expedição (dd/mm/aaaa)', '01/01/2024')
    
    cert_letter = cert_letters[cert_index]
    cert_index += 1
    certificates.append(f"{cert_letter}) A Certidão Negativa de Citações de Ações Reais e Pessoais Reipersecutórias e Ônus Reais, fornecida pelo Cartório do {office_number}º Ofício da Comarca de {city}-ES, datada de {onus_date}, onde o mesmo se acha livre de ônus;")
    
    # B-D) Indisponibilidade (one per party - both vendors and buyers)
    all_parties = session.get("vendedores", []) + session.get("compradores", [])
    for party in all_parties:
        if party.get("tipo") == "Pessoa Física":
            # Look for indisponibilidade data for this party
            party_name = party.get("nome_completo", "NOME")
            party_cpf = party.get("cpf", "000.000.000-00")
            
            # Generate hash code for indisponibilidade
            hash_code = generate_hash_code()
            
            cert_letter = cert_letters[cert_index]
            cert_index += 1
            certificates.append(f'{cert_letter}) Consulta a base de dados da Central Nacional de Indisponibilidade de Bens - CNIB, aos [DATE] às [TIME], em nome de {party_name}, CPF n° {party_cpf}, tendo a informação de "nenhum resultado encontrado para o filtro selecionado" e o código de HASH {hash_code};')
    
    # Process per-vendor certificates (SHARED and RURAL-ONLY)
    vendedores = session.get("vendedores", [])
    for vendor_idx, vendedor in enumerate(vendedores):
        if vendedor.get("tipo") == "Pessoa Física":
            vendor_name = vendedor.get("nome_completo", "VENDEDOR")
            vendor_cpf = vendedor.get("cpf", "000.000.000-00")
            
            # Shared certificates (same format as urban)
            shared_certs = ["negativa_federal", "debitos_tributarios", "negativa_estadual", "debitos_trabalhistas"]
            
            for cert_type in shared_certs:
                cert_data = session.get('certidoes', {}).get(f'{cert_type}_{vendor_idx}', {})
                
                if cert_data.get('dispensa'):
                    # Handle dispensed certificates
                    cert_letter = cert_letters[cert_index]
                    cert_index += 1
                    if cert_type == "negativa_federal":
                        certificates.append(f"{cert_letter}) Não pôde ser emitida a Certidão Conjunta Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União, em nome de {vendor_name}, pela Internet por meio do endereço www.receita.fazenda.gov.br, aos [DATE], dispensando os Outorgados Compradores a apresentação da mesma;")
                else:
                    # Handle presented certificates
                    cert_letter = cert_letters[cert_index]
                    cert_index += 1
                    if cert_type == "negativa_federal":
                        cert_number = cert_data.get("Número da Certidão", "000000")
                        cert_date = cert_data.get("Data de emissão", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão Conjunta Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União, nº {cert_number}, em nome de {vendor_name}, pela Internet por meio do endereço www.receita.fazenda.gov.br, aos {cert_date};")
                    elif cert_type == "debitos_tributarios":
                        cert_date = cert_data.get("Dia de emissão (dd/mm/aaaa)", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão de Débitos Tributários, em nome de {vendor_name}, CPF {vendor_cpf}, expedida pela Secretaria da Fazenda, pela Internet por meio do endereço www.sefaz.es.gov.br, aos {cert_date};")
                    elif cert_type == "negativa_estadual":
                        cert_number = cert_data.get("Número da Certidão", "000000")
                        cert_date = cert_data.get("Data de emissão", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão Negativa de Débitos para a Fazenda Pública Estadual, nº {cert_number} para o CPF {vendor_cpf}, em nome de {vendor_name}, expedida pela Secretaria de Estado da Fazenda, pela Internet por meio do endereço www.sefaz.es.gov.br, aos {cert_date};")
                    elif cert_type == "debitos_trabalhistas":
                        cert_number = cert_data.get("Número da Certidão", "000000")
                        cert_date = cert_data.get("Data de Emissão (dd/mm/aaaa)", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão Negativa de Débitos Trabalhistas, expedida pelo Tribunal Superior de Justiça do Trabalho, de n° {cert_number}, em nome de {vendor_name}, pela Internet por meio do endereço www.cndt@tst.jus.br, aos {cert_date};")
            
            # RURAL-ONLY certificates per vendor
            rural_certs = ["execucoes_fiscais", "distribuicao_acoes", "ibama"]
            
            for cert_type in rural_certs:
                cert_data = session.get('certidoes', {}).get(f'{cert_type}_{vendor_idx}', {})
                
                if not cert_data.get('dispensa'):
                    cert_letter = cert_letters[cert_index]
                    cert_index += 1
                    if cert_type == "execucoes_fiscais":
                        cert_number = cert_data.get("Numero da Certidão", "000000")
                        cert_date = cert_data.get("Data de expedição (dd/mm/aaaa)", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão Negativa de Execuções Fiscais, emitida pelo Tribunal de Justiça do Estado do Espírito Santo, nº {cert_number}, em nome de {vendor_name}, pela Internet por meio do endereço www.tjes.jus.br, aos {cert_date};")
                    elif cert_type == "distribuicao_acoes":
                        cert_number = cert_data.get("Numero da Certidão", "000000")
                        cert_date = cert_data.get("Data de expedição (dd/mm/aaaa)", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão de Distribuição Ações e Execuções, expedida pela Justiça Federal, nº {cert_number}, em nome de {vendor_name}, pela Internet por meio do endereço www.jfes.jus.br, aos {cert_date};")
                    elif cert_type == "ibama":
                        cert_number = cert_data.get("Numero da Certidão", "000000")
                        cert_date = cert_data.get("Data de expedição (dd/mm/aaaa)", "01/01/2024")
                        certificates.append(f"{cert_letter}) A Certidão Negativa de Débitos do IBAMA, de nº {cert_number}, em nome de {vendor_name}, expedida pelo Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis, pela Internet por meio do endereço www.ibama.gov.br, aos {cert_date};")
    
    # Property-level certificates (RURAL-ONLY)
    # ITR
    itr = session.get('certidoes', {}).get('itr', {})
    if itr:
        cib_number = itr.get('Numero do CIB', 'CIB_NUMBER')
        control_code = itr.get('Codigo de controle', 'CTRL_CODE')
        issue_date = itr.get('Data de expedição (dd/mm/aaaa)', '01/01/2024')
        valid_until = itr.get('Data de Validade(dd/mm/aaaa)', '31/12/2024')
        
        cert_letter = cert_letters[cert_index]
        cert_index += 1
        certificates.append(f"{cert_letter}) A Certidão Negativa de Débitos Relativos ao Imposto sobre a Propriedade Territorial Rural, emitida pela Secretaria da Receita Federal do Brasil, sob o CIB nº. {cib_number}; código de controle {control_code}, aos {issue_date}, com validade até {valid_until}, pela Internet por meio do endereço www.receita.fazenda.gov.br;")
    
    # CCIR
    ccir = session.get('certidoes', {}).get('ccir', {})
    if ccir:
        ccir_number = ccir.get('Numero do Certificado', 'CCIR_NUMBER')
        
        cert_letter = cert_letters[cert_index]
        cert_index += 1
        certificates.append(f"{cert_letter}) O CCIR 2025 (Certificado de Cadastro de Imóvel Rural), emitido pelo Instituto Nacional de Colonização e Reforma Agrária-INCRA, sob o nº {ccir_number};")
    
    # ITBI
    cert_letter = cert_letters[cert_index]
    cert_index += 1
    city = session.get('certidoes', {}).get('onus', {}).get('Município do imóvel', 'MUNICÍPIO')
    certificates.append(f"{cert_letter}) Será apresentada quitada, no ato do registro, a Guia de Transmissão, emitida pela Secretaria Municipal da Fazenda de {city}-ES, referente ao ITBI, a base de 1% (um por cento) sobre o valor do imóvel.")
    
    return "\n\n".join(certificates)

def format_birth_date(date_str: str) -> str:
    """Convert dates to Portuguese format like '13 de agosto de 1961'"""
    try:
        if '/' in date_str:
            day, month, year = date_str.split('/')
        elif '-' in date_str:
            year, month, day = date_str.split('-')
        else:
            return date_str
        
        months_pt = {
            '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril',
            '05': 'maio', '06': 'junho', '07': 'julho', '08': 'agosto',
            '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro'
        }
        
        month_name = months_pt.get(month.zfill(2), 'mês')
        return f"{int(day)} de {month_name} de {year}"
    except:
        return date_str

def format_marriage_date(date_str: str) -> str:
    """Format marriage date with both written and numeric format"""
    try:
        if '/' in date_str:
            day, month, year = date_str.split('/')
        elif '-' in date_str:
            year, month, day = date_str.split('-')
        else:
            return date_str
            
        months_pt = {
            '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril',
            '05': 'maio', '06': 'junho', '07': 'julho', '08': 'agosto',
            '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro'
        }
        
        month_name = months_pt.get(month.zfill(2), 'mês')
        formatted_date = f"{int(day)} de {month_name} de {year}"
        numeric_date = f"({day.zfill(2)}/{month.zfill(2)}/{year})"
        return f"{formatted_date} {numeric_date}"
    except:
        return date_str

def spell_out_area(area_str: str) -> str:
    """Convert area numbers to Portuguese text"""
    try:
        # Clean the input
        area_clean = str(area_str).replace(',', '.').replace(' ', '').replace('m²', '').replace('m', '')
        area_num = float(area_clean)
        area_int = int(area_num) if area_num == int(area_num) else area_num
        
        # Basic number to words mapping (simplified for common cases)
        units = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
        teens = ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove']
        tens = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
        hundreds = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
        
        if area_int == 0:
            return "zero metros quadrados"
        elif area_int < 10:
            return f"{units[area_int]} metros quadrados"
        elif area_int < 20:
            return f"{teens[area_int - 10]} metros quadrados"
        elif area_int < 100:
            tens_digit = area_int // 10
            units_digit = area_int % 10
            if units_digit == 0:
                return f"{tens[tens_digit]} metros quadrados"
            else:
                return f"{tens[tens_digit]} e {units[units_digit]} metros quadrados"
        elif area_int < 1000:
            hundreds_digit = area_int // 100
            remainder = area_int % 100
            if remainder == 0:
                return f"{hundreds[hundreds_digit]} metros quadrados"
            elif remainder < 10:
                return f"{hundreds[hundreds_digit]} e {units[remainder]} metros quadrados"
            elif remainder < 20:
                return f"{hundreds[hundreds_digit]} e {teens[remainder - 10]} metros quadrados"
            else:
                tens_digit = remainder // 10
                units_digit = remainder % 10
                if units_digit == 0:
                    return f"{hundreds[hundreds_digit]} e {tens[tens_digit]} metros quadrados"
                else:
                    return f"{hundreds[hundreds_digit]}, {tens[tens_digit]} e {units[units_digit]} metros quadrados"
        else:
            # For larger numbers, just return the numeric value
            return f"{area_int} metros quadrados"
    except:
        return f"{area_str} metros quadrados"

def spell_out_currency(value_str: str) -> str:
    """Convert currency values to Portuguese text"""
    try:
        # Extract numeric value from currency string
        clean_value = value_str.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', '')
        value_num = float(clean_value)
        
        # Simplified currency spelling (for common values)
        if value_num == 100000:
            return "cem mil reais"
        elif value_num == 250000:
            return "duzentos e cinquenta mil reais"
        elif value_num == 500000:
            return "quinhentos mil reais"
        elif value_num == 1000000:
            return "um milhão de reais"
        else:
            # For other values, return a simplified version
            int_value = int(value_num)
            return f"{int_value} reais"
    except:
        return "valor em reais"

def generate_hash_code() -> str:
    """Generate random 10-character hash codes for certificates"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def count_effective_people(parties: List[Dict]) -> int:
    """Count the effective number of people including signing spouses (from working OLDAPP.py)"""
    total_people = 0
    
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            total_people += 1  # The party themselves
            # Add spouse if they sign the document
            if party.get("casado") and party.get("conjuge_assina"):
                total_people += 1
        else:
            # Pessoa Jurídica counts as 1
            total_people += 1
    
    return total_people

def determine_gender_suffix(parties: List[Dict], is_vendedor: bool) -> Dict[str, str]:
    """Determine the correct gender suffixes based on the parties (FIXED: Using comprehensive logic from working OLDAPP.py)"""
    if not parties:
        return {
            "title": "VENDEDOR" if is_vendedor else "COMPRADOR",
            "article": "o",
            "plural": "",
            "possessive": "or"
        }
    
    # Check if any party is Pessoa Jurídica (companies are feminine in Brazilian legal language)
    has_company = any(party.get("tipo") == "Pessoa Jurídica" for party in parties)
    
    # Count males and females (for physical persons only) - improved gender detection
    # IMPORTANT: Include signing spouses in the count
    males = 0
    females = 0
    
    for p in parties:
        if p.get("tipo") == "Pessoa Física":
            # Count the main person
            gender = p.get("sexo", "").lower()
            if gender in ['masculino', 'm', 'male']:
                males += 1
            elif gender in ['feminino', 'f', 'female']:
                females += 1
            else:
                # Fallback: no explicit gender found, default to masculine
                males += 1
            
            # Count signing spouse
            if p.get("casado") and p.get("conjuge_assina") and p.get("conjuge_data"):
                spouse_gender = p["conjuge_data"].get("sexo", "").lower()
                if spouse_gender in ['masculino', 'm', 'male']:
                    males += 1
                elif spouse_gender in ['feminino', 'f', 'female']:
                    females += 1
                else:
                    # Fallback: no explicit gender found, default to masculine
                    males += 1
    
    # Use effective people count (including signing spouses)
    total_effective_people = count_effective_people(parties)
    physical_persons = sum(1 for p in parties if p.get("tipo") == "Pessoa Física")
    
    if total_effective_people == 1:
        # Single person (no signing spouse)
        if has_company:
            # Single company - always feminine
            return {
                "title": "VENDEDORA" if is_vendedor else "COMPRADORA",
                "article": "a",
                "plural": "",
                "possessive": "ora"
            }
        elif females > 0 and males == 0:
            # Single female person
            return {
                "title": "VENDEDORA" if is_vendedor else "COMPRADORA",
                "article": "a",
                "plural": "",
                "possessive": "ora"
            }
        else:
            # Single male person (or default)
            return {
                "title": "VENDEDOR" if is_vendedor else "COMPRADOR",
                "article": "o",
                "plural": "",
                "possessive": "or"
            }
    else:
        # Multiple people (including cases with signing spouse) - always use plural forms
        if has_company and physical_persons == 0:
            # Only companies - feminine plural
            return {
                "title": "VENDEDORAS" if is_vendedor else "COMPRADORAS",
                "article": "as",
                "plural": "s",
                "possessive": "ras"
            }
        elif males > 0:
            # At least one male (mixed or all male) - masculine plural (Brazilian grammar rule)
            return {
                "title": "VENDEDORES" if is_vendedor else "COMPRADORES",
                "article": "os",
                "plural": "s",
                "possessive": "res"
            }
        else:
            # All female persons or mix of companies and females - feminine plural
            return {
                "title": "VENDEDORAS" if is_vendedor else "COMPRADORAS",
                "article": "as",
                "plural": "s",
                "possessive": "ras"
            }

def get_gender_agreement(person: Dict[str, Any]) -> Dict[str, str]:
    """Get gender agreement for participles based on person's gender (from working OLDAPP.py)"""
    gender = person.get("sexo", "").lower()
    if gender in ['feminino', 'f', 'female']:
        return {
            "nascido": "Nascida",
            "inscrito": "Inscrita",
            "portador": "Portadora"
        }
    else:
        # Default to masculine for unknown or male
        return {
            "nascido": "Nascido",
            "inscrito": "Inscrito",
            "portador": "Portador"
        }

def format_parties(parties: List[Dict]) -> str:
    """Format party information for the deed (FIXED: Using comprehensive formatting from working OLDAPP.py)"""
    formatted = []
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            # Get gender agreements for this person
            gender_agreement = get_gender_agreement(party)
            
            # Remove quotes from names for proper legal formatting
            text = f'{party.get("nome_completo", "")}, {gender_agreement["nascido"]} em, {party.get("data_nascimento", "")}'
            
            if party.get("documento_tipo") == "Carteira de Identidade" and party.get("cpf"):
                text += f', {gender_agreement["inscrito"]} no Cadastro de Pessoas Físicas sob o número "{party.get("cpf")}"'
            elif party.get("documento_tipo") == "CNH" and party.get("cnh_numero"):
                text += f', com CNH n°{party.get("cnh_numero")} expedida em {party.get("cnh_orgao_expedidor", "")}'
            elif party.get("documento_tipo") == "Carteira de Trabalho" and party.get("ctps_numero"):
                text += f', {gender_agreement["portador"]} da CTPS n° {party.get("ctps_numero")} série {party.get("ctps_serie", "")}-ES'
            
            if party.get("casado") and party.get("regime_bens"):
                text += f', casado sob o regime de {party.get("regime_bens")}'
                if party.get("conjuge_assina") and party.get("conjuge_data"):
                    conj = party["conjuge_data"]
                    # Get gender agreements for spouse
                    conj_gender_agreement = get_gender_agreement(conj)
                    text += f' com {conj.get("nome_completo", "")}, {conj_gender_agreement["nascido"]} em, {conj.get("data_nascimento", "")}'
                    if conj.get("cpf"):
                        text += f', {conj_gender_agreement["inscrito"]} no Cadastro de Pessoas Físicas sob o número "{conj.get("cpf")}"'
                    elif conj.get("cnh_numero"):
                        text += f', com CNH n°{conj.get("cnh_numero")} expedida em {conj.get("cnh_orgao_expedidor", "")}'
                    elif conj.get("ctps_numero"):
                        text += f', {conj_gender_agreement["portador"]} da CTPS n° {conj.get("ctps_numero")} série {conj.get("ctps_serie", "")}-ES'
            
            formatted.append(text)
        else:
            # Pessoa Jurídica
            razao_social = party.get("razao_social", "***EMPRESA***")
            cnpj = party.get("cnpj", "***CNPJ***")
            endereco = party.get("endereco", "")
            
            text = f'{razao_social}, pessoa jurídica de direito privado, inscrita no CNPJ sob o nº {cnpj}'
            if endereco:
                text += f', com sede em {endereco}'
                
            formatted.append(text)
    
    return "; ".join(formatted)

def format_certificates_section(session: Dict[str, Any]) -> str:
    """Format the certificates section of the deed - grouped by certificate type (from working OLDAPP.py)"""
    cert_text = """

**1º) IMPOSTO DE TRANSMISSÃO** - Nos termos do artigo 620, II, e § 1º, do Código de Normas da Corregedoria Geral da Justiça do Estado do Espírito Santo, o comprovante de quitação do Imposto de Transmissão Sobre Bens Imóveis (ITBI) será apresentado por ocasião do registro do presente instrumento no cartório de registro de imóveis competente, conforme previsto nos artigos 1.245 do Código Civil Brasileiro e 35 do Código Tributário Nacional e em consonância com a DECISÃO/OFÍCIO 0438046/7006509-62.2019.2.00.0000 da E. Corregedoria Geral da Justiça deste Estado; devidamente cadastrado na Prefeitura Municipal de <CIDADE> sob o n.º ***NUMERO*;**"""
    
    cert_counter = 2
    certidoes = session.get("certidoes", {})
    vendedores = session.get("vendedores", [])
    
    # Certidão de Ônus
    if "onus" in certidoes:
        cert = certidoes["onus"]
        cert_text += f"""

**{cert_counter}º)** **CERTIDÃO NEGATIVA DE ÔNUS E AÇÕES REAIS E PESSOAIS REIPERSECUTÓRIA**, expedida em **{cert.get('Data de expedição (dd/mm/aaaa)', '***')}**, pelo {cert.get('Cartório de Expedição (nome completo)', '***')}. Ass: {cert.get('Nome completo de quem assinou', '***')}"""
        cert_counter += 1
    
    # Group certificates by type, then by vendedor
    cert_types = [
        ("negativa_federal", "CERTIDÃO NEGATIVA DE DÉBITO MUNICIPAL", "CERTIDÃO NEGATIVA DE DÉBITOS IMOBILIÁRIOS"),
        ("debitos_tributarios", "CERTIDÃO NEGATIVA FEDERAL", "CERTIDÃO DE DÉBITOS RELATIVOS A CRÉDITOS TRIBUTÁRIOS FEDERAIS E À DÍVIDA ATIVA DA UNIÃO"),
        ("negativa_estadual", "CERTIDÃO NEGATIVA ESTADUAL", "CERTIDÃO NEGATIVA PARA COM A FAZENDA PÚBLICA ESTADUAL"),
        ("debitos_trabalhistas", "CERTIDÃO DE DÉBITOS TRABALHISTAS", "CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS"),
        ("indisponibilidade", "RELATÓRIO DE CONSULTA DE INDISPONIBILIDADE", "RELATÓRIO DE CONSULTA DE INDISPONIBILIDADE")
    ]
    
    for cert_type, dispensa_title, cert_title in cert_types:
        # Process each vendedor for this certificate type
        for v_idx, vendedor in enumerate(vendedores):
            vendedor_name = vendedor.get("nome_completo", f"Vendedor {v_idx + 1}")
            cert_key = f"{cert_type}_{v_idx}"
            
            if cert_key in certidoes:
                if certidoes[cert_key].get("dispensa"):
                    # Handle dispensed certificates
                    if cert_type == "negativa_federal":
                        cert_text += f"""

**{cert_counter}º) {dispensa_title}** - Os outorgados compradores dispensam a apresentação da certidão negativa de débitos municipais do imóvel, conforme faculta o Decreto n° 93.240 de 9 de setembro de 1986, Art. 1°, parágrafo 2° e o artigo 643 do Código de Normas da CGJ/ES, estando os mesmos cientes de que, neste caso, se responsabilizam nos termos da lei, pelo pagamento dos débitos fiscais existentes;"""
                    elif cert_type == "debitos_tributarios":
                        cert_text += f"""

**{cert_counter}º) {dispensa_title}** - Os outorgados compradores dispensam a apresentação da certidão negativa de débitos federais e, considerando que a outorgante vendedora declara que exerce exclusivamente as atividades de compra e venda de imóveis, locação, desmembramento ou loteamento de terrenos, incorporação imobiliária e/ou construção de imóveis destinados à venda e que o imóvel objeto da presente está contabilmente lançado no ativo circulante e não consta, nem nunca constou, do ativo permanente da empresa, fica dispensada a apresentação da CND nos termos do art. 17, I, da portaria conjunta PGFN/RFB nº 1.751, de 02/10/2014;"""
                    elif cert_type == "negativa_estadual":
                        cert_text += f"""

**{cert_counter}º) {dispensa_title}** - Os outorgados compradores dispensam a apresentação da certidão negativa de débitos perante a Fazenda Pública Estadual;"""
                    elif cert_type == "debitos_trabalhistas":
                        cert_text += f"""

**{cert_counter}º) {dispensa_title}** ({vendedor_name}) - DISPENSADA"""
                else:
                    # Handle actual certificates
                    cert = certidoes[cert_key]
                    
                    if cert_type == "negativa_federal":
                        cert_text += f"""

**{cert_counter}º) {cert_title}** - nº {cert.get('Número da Certidão', '***')} - Prefeitura Municipal de {cert.get('Município', '***')}- ES - Secretaria Municipal de Finanças, emitida em {cert.get('Data de emissão', '***')}- VIA INTERNET - valida por 30 dias - Código de Controle de autenticidade nº {cert.get('Número do código de autenticidade', '***')} - Confirmada a sua validade na Internet no endereço: www.***.es.gov.br;"""
                    elif cert_type == "debitos_tributarios":
                        cert_text += f"""

**{cert_counter}º) {cert_title}** - Nome: {cert.get('Nome completo', '***')}. CPF: {cert.get('CPF', '***')} Certidão emitida gratuitamente com base na Portaria Conjunta RFB/PGFN nº 1.751, de 2/10/2014. Emitida às {cert.get('Hora de emissão', '***')} do dia {cert.get('Dia de emissão (dd/mm/aaaa)', '***')}. Válida até {cert.get('Data de validade (dd/mm/aaaa)', '***')}. Código de controle da certidão: {cert.get('Código de controle da certidão', '***')};"""
                    elif cert_type == "negativa_estadual":
                        cert_text += f"""

**{cert_counter}º) {cert_title}** - MOD.2 ({cert.get('Nome completo', '***')}) N. {cert.get('Número da Certidão', '***')} - Secretaria de Estado da Fazenda Governo do Estado do Espírito Santo - emitida em {cert.get('Data de emissão', '***')} - valida até {cert.get('Data de emissão', '***')} - Autenticação Eletrônica: {cert.get('Número do código de autenticidade', '***')} - Confirmada a sua validade na Internet no endereço: www.sefaz.es.gov.br;"""
                    elif cert_type == "debitos_trabalhistas":
                        if vendedor.get("tipo") == "Pessoa Jurídica":
                            # Format for Pessoa Jurídica
                            cert_text += f"""

**{cert_counter}º) {cert_title}** -  nº "{cert.get('Número da Certidão', '***')}"  - Certifica-se que ({cert.get('Nome Completo', '***')}), inscrita no CNPJ sob o nº "{cert.get('CPF', '***')}", NÃO CONSTA do Banco Nacional de Devedores Trabalhistas, emitida em "{cert.get('Data de Emissão (dd/mm/aaaa)', '***')}", às "{cert.get('Horário de Emissão (hh:mm)', '***')}" - válida até "{cert.get('Validade da Certidão(dd/mm/aaaa)', '***')}"" - Confirmada a sua validade na internet no endereço: www.tst.jus.br;"""
                        else:
                            # Format for Pessoa Física (existing format)
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - nº {cert.get('Número da Certidão', '***')} - Certifica-se que {cert.get('Nome Completo', '***')}, inscrito no CPF/MF sob o nº {cert.get('CPF', '***')}, NÃO CONSTA do Banco Nacional de Devedores Trabalhistas, emitida em {cert.get('Data de Emissão (dd/mm/aaaa)', '***')} às {cert.get('Horário de Emissão (hh:mm)', '***')} hs - válida até {cert.get('Validade da Certidão(dd/mm/aaaa)', '***')} - Confirmada a sua validade na internet no endereço: www.tst.jus.br;"""
                    elif cert_type == "indisponibilidade":
                        if vendedor.get("tipo") == "Pessoa Jurídica":
                            # Format for Pessoa Jurídica
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - PROVIMENTO Nº 39/2014: CNPJ pesquisado "{cert.get('CNPJ', '***')}" de *"{cert.get('Nome da Empresa', '***')}"- ME (-----------) na data : "{cert.get('Data da Consulta', '***')}" às "{cert.get('Hora da Consulta', '***')}". RESULTADO: NEGATIVO – código "{cert.get('Código HASH', '***')}" """
                        else:
                            # Format for Pessoa Física (existing format)
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - PROVIMENTO Nº 39/2014: ***** RESULTADO: **NEGATIVO.** CODIGO HASH: {cert.get('Código HASH', '***')} ;"""
                
                cert_counter += 1
    
    # Add condominium declaration only for Apto (not for Lote)
    if session.get("tipo_escritura") != "Escritura de Lote":
        condominio_data = certidoes.get("condominio", {})
        
        if condominio_data.get("dispensa"):
            # Use generic format when dispensa is used
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de *****************. Ass: **************** - Síndico;"""
        elif condominio_data:
            # Use specific data when declaration was uploaded (CRITICAL FIX: Use correct field names)
            data_documento = condominio_data.get("Data do documento (dd/mm/aaaa)", "*****************")
            nome_sindico = condominio_data.get("Nome Completo do Síndico", "****************")
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de "{data_documento}" Ass: "{nome_sindico}." - Síndico;"""
        else:
            # Default format (fallback)
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de *****************. Ass: **************** - Síndico;"""
    
    return cert_text

# Main endpoint
@app.route('/process', methods=['POST'])
def process_document():
    """Single endpoint that handles the entire document processing flow"""
    
    try:
        # Log incoming request details for debugging
        app.logger.info(f"DEBUG: Process request received. Content-Type: {request.content_type}")
        app.logger.info(f"DEBUG: Form keys: {list(request.form.keys())}")
        app.logger.info(f"DEBUG: Files keys: {list(request.files.keys())}")
        
        # Get form data
        session_id = request.form.get('session_id')
        response = request.form.get('response')
        file = request.files.get('file')
        
        app.logger.info(f"DEBUG: session_id={session_id}, response={response}, file={file}")
        
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
                # Check if this is a rural escritura and use appropriate template generator
                if session.get('is_rural'):
                    result = process_all_rural_documents(session)
                else:
                    result = process_all_documents(session)
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
            
            # Process document with OCR
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            
            # Extract data based on document type (FIXED: Using correct field mappings from OLDAPP.py)
            doc_type = session["temp_data"].get("documento_tipo")
            if doc_type == "Carteira de Identidade":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            elif doc_type == "CNH":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            else:  # Carteira de Trabalho
                prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            
            extracted = extract_data_with_gemini(text, prompt)
            
            # Store comprador data (CRITICAL FIX: Use actual field names returned by Gemini)
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
        
        elif current_step == "comprador_empresa_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            # Process company document with OCR (from working OLDAPP.py)
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            app.logger.info(f"COMPRADOR EMPRESA DEBUG: Extracted text length: {len(text)}")
            app.logger.info(f"COMPRADOR EMPRESA DEBUG: Text sample: {repr(text[:200])}")
            
            # Extract company data
            prompt = "Razão Social (Nome da Empresa), CNPJ (formato XX.XXX.XXX/XXXX-XX), Endereço da Empresa"
            app.logger.info(f"COMPRADOR EMPRESA DEBUG: Using prompt: {prompt}")
            extracted = extract_data_with_gemini(text, prompt)
            app.logger.info(f"COMPRADOR EMPRESA DEBUG: Extraction result: {extracted}")
            
            # Store empresa data (CRITICAL FIX: Use actual field names)
            empresa = {
                "tipo": "Pessoa Jurídica",
                "razao_social": extracted.get("Razão Social (Nome da Empresa)", ""),
                "cnpj": extracted.get("CNPJ (formato XX.XXX.XXX/XXXX-XX)", ""),
                "endereco": extracted.get("Endereço da Empresa", ""),
                "casado": False  # Companies don't have marriage status
            }
            
            session["temp_data"]["current_comprador"] = empresa
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "comprador_casado":
            session["temp_data"]["current_comprador"]["casado"] = (response == "Sim")
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "certidao_casamento_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            prompt = "1: Regime de Bens do Casamento"
            extracted = extract_data_with_gemini(text, prompt)
            
            session["temp_data"]["current_comprador"]["regime_bens"] = extracted.get("Regime de Bens do Casamento", "")
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "conjuge_assina":
            session["temp_data"]["current_comprador"]["conjuge_assina"] = (response == "Sim")
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "conjuge_documento_tipo":
            session["temp_data"]["conjuge_doc_tipo"] = response
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "conjuge_documento_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            
            doc_type = session["temp_data"].get("conjuge_doc_tipo")
            if doc_type == "Carteira de Identidade":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            elif doc_type == "CNH":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            else:  # Carteira de Trabalho
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Série da Carteira, 4: Número da Carteira, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            
            extracted = extract_data_with_gemini(text, prompt)
            
            conjuge_data = {
                "nome_completo": extracted.get("Nome Completo", ""),
                "data_nascimento": extracted.get("Data de Nascimento", ""),
                "documento_tipo": doc_type
            }
            
            if doc_type == "Carteira de Identidade":
                conjuge_data["cpf"] = extracted.get("Número do CPF", "")
                conjuge_data["sexo"] = extracted.get("Gênero", "")
            elif doc_type == "CNH":
                conjuge_data["cnh_numero"] = extracted.get("Número da CNH", "")
                conjuge_data["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
                conjuge_data["sexo"] = extracted.get("Gênero", "")
            else:  # Carteira de Trabalho
                conjuge_data["ctps_serie"] = extracted.get("Série da Carteira", "")
                conjuge_data["ctps_numero"] = extracted.get("Número da Carteira", "")
                conjuge_data["sexo"] = extracted.get("Gênero", "")
            
            session["temp_data"]["current_comprador"]["conjuge_data"] = conjuge_data
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "mais_compradores":
            # Always save current comprador before proceeding (like working version)
            if "current_comprador" in session["temp_data"]:
                session["compradores"].append(session["temp_data"]["current_comprador"])
                session["temp_data"]["current_comprador"] = None
            
            session["current_step"] = determine_next_step(session, response)
        
        # Similar processing for vendedor steps...
        elif current_step == "vendedor_tipo":
            session["temp_data"]["tipo_pessoa"] = response
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "vendedor_documento_tipo":
            session["temp_data"]["documento_tipo"] = response
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "vendedor_documento_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            
            doc_type = session["temp_data"].get("documento_tipo")
            if doc_type == "Carteira de Identidade":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            elif doc_type == "CNH":
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            else:  # Carteira de Trabalho
                prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Série da Carteira, 4: Número da Carteira, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
            
            extracted = extract_data_with_gemini(text, prompt)
            
            vendedor = {
                "tipo": "Pessoa Física",
                "nome_completo": extracted.get("Nome Completo", ""),
                "data_nascimento": extracted.get("Data de Nascimento", ""),
                "documento_tipo": doc_type
            }
            
            if doc_type == "Carteira de Identidade":
                vendedor["cpf"] = extracted.get("Número do CPF", "")
                vendedor["sexo"] = extracted.get("Gênero", "")
            elif doc_type == "CNH":
                vendedor["cnh_numero"] = extracted.get("Número da CNH", "")
                vendedor["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
                vendedor["sexo"] = extracted.get("Gênero", "")
            else:  # Carteira de Trabalho
                vendedor["ctps_serie"] = extracted.get("Série da Carteira", "")
                vendedor["ctps_numero"] = extracted.get("Número da Carteira", "")
                vendedor["sexo"] = extracted.get("Gênero", "")
            
            session["temp_data"]["current_vendedor"] = vendedor
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "vendedor_empresa_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            # Process company document with OCR (from working OLDAPP.py)
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            app.logger.info(f"VENDEDOR EMPRESA DEBUG: Extracted text length: {len(text)}")
            app.logger.info(f"VENDEDOR EMPRESA DEBUG: Text sample: {repr(text[:200])}")
            
            # Extract company data
            prompt = "Razão Social (Nome da Empresa), CNPJ (formato XX.XXX.XXX/XXXX-XX), Endereço da Empresa"
            app.logger.info(f"VENDEDOR EMPRESA DEBUG: Using prompt: {prompt}")
            extracted = extract_data_with_gemini(text, prompt)
            app.logger.info(f"VENDEDOR EMPRESA DEBUG: Extraction result: {extracted}")
            
            # Store empresa data (CRITICAL FIX: Use actual field names)
            empresa = {
                "tipo": "Pessoa Jurídica",
                "razao_social": extracted.get("Razão Social (Nome da Empresa)", ""),
                "cnpj": extracted.get("CNPJ (formato XX.XXX.XXX/XXXX-XX)", ""),
                "endereco": extracted.get("Endereço da Empresa", ""),
                "casado": False  # Companies don't have marriage status
            }
            
            session["temp_data"]["current_vendedor"] = empresa
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "vendedor_casado":
            session["temp_data"]["current_vendedor"]["casado"] = (response == "Sim")
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "vendedor_certidao_casamento_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            prompt = "1: Regime de Bens do Casamento"
            extracted = extract_data_with_gemini(text, prompt)
            
            session["temp_data"]["current_vendedor"]["regime_bens"] = extracted.get("Regime de Bens do Casamento", "")
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "mais_vendedores":
            # Always save current vendedor before proceeding (like working version)
            if "current_vendedor" in session["temp_data"]:
                session["vendedores"].append(session["temp_data"]["current_vendedor"])
                session["temp_data"]["current_vendedor"] = None
            session["current_step"] = determine_next_step(session, response)
        
        # Certificate processing
        elif current_step == "certidao_onus_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            
            # Check if this is a rural escritura and use extended prompt
            if session.get('is_rural'):
                # Rural Ônus needs MORE fields for rural property description
                prompt = """Data de expedição (dd/mm/aaaa), 
Cartório de Expedição (nome completo), 
Nome completo de quem assinou,
Número do Ofício (apenas o número, ex: 1, 2, 3),
Cidade do Cartório,
Número da Matrícula do Registro,
Número do Livro,
Localização do imóvel rural,
Município do imóvel,
Área total em m²,
Nome do proprietário ao Norte,
Nome do proprietário ao Sul,
Nome do proprietário ao Leste,
Nome do proprietário ao Oeste,
Nome da propriedade (ex: Sítio da Vitória)"""
            else:
                # Use existing urban prompt
                prompt = """Data de expedição (dd/mm/aaaa), 
Cartório de Expedição (nome completo), 
Nome completo de quem assinou,
Descrição breve do imóvel,
Número do Ofício (apenas o número, ex: 1, 2, 3),
Zona do Cartório (ex: 1ª Zona, 2ª Zona),
Cidade do Cartório,
Número da Matrícula do Registro,
Número do Livro"""
            
            extracted = extract_data_with_gemini(text, prompt)
            
            session["certidoes"]["onus"] = extracted
            
            # For rural, mark Ônus as processed and proceed to rural flow
            if session.get('is_rural'):
                session["temp_data"]["onus_processed"] = True
                # Initialize vendedor tracking for rural certificates
                session["temp_data"]["vendedor_idx"] = 0
                session["temp_data"]["cert_type"] = "negativa_federal"
                session["temp_data"]["cert_name"] = "Certidão Negativa Federal"
                session["current_step"] = "certidao_negativa_federal_option"
            else:
                session["current_step"] = determine_next_step(session, response)
        
        elif current_step.startswith("certidao_") and current_step.endswith("_option"):
            if response == "Usar Dispensa":
                cert_type = session["temp_data"]["cert_type"]
                vendedor_idx = session["temp_data"]["vendedor_idx"]
                session["certidoes"][f"{cert_type}_{vendedor_idx}"] = {"dispensa": True}
                
                # Route to appropriate flow for next step
                if session.get('is_rural'):
                    session["current_step"] = get_next_rural_certificate_step(session)
                else:
                    session["current_step"] = determine_next_step(session, response)
            else:
                # "Apresentar Certidão" - go to upload step for current certificate
                session["current_step"] = current_step.replace("_option", "_upload")
        
        elif current_step.startswith("certidao_") and current_step.endswith("_upload"):
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            
            cert_type = session["temp_data"]["cert_type"]
            vendedor_idx = session["temp_data"]["vendedor_idx"]
            
            # Define prompts for each certificate type (CRITICAL FIX: Remove numbers, use field names)
            prompts = {
                # SHARED certificates (reuse existing urban extraction)
                "negativa_federal": "Número da Certidão, Município, Data de emissão, Número do código de autenticidade",
                "debitos_tributarios": "Nome completo, CPF, Hora de emissão, Dia de emissão (dd/mm/aaaa), Data de validade (dd/mm/aaaa), Código de controle da certidão",
                "negativa_estadual": "Número da Certidão, Município, Data de emissão, Número do código de autenticidade, Nome completo",
                "debitos_trabalhistas": "Número da Certidão, Nome Completo, CPF, Data de Emissão (dd/mm/aaaa), Horário de Emissão (hh:mm), Validade da Certidão(dd/mm/aaaa)",
                "indisponibilidade": "Código HASH",
                # RURAL-ONLY certificates (new extraction needed)
                "execucoes_fiscais": "Numero da Certidão, Nome completo, Data de expedição (dd/mm/aaaa)",
                "distribuicao_acoes": "Numero da Certidão, Nome completo, Data de expedição (dd/mm/aaaa)",
                "itr": "Numero do CIB, Codigo de controle, Data de expedição (dd/mm/aaaa), Data de Validade(dd/mm/aaaa)",
                "ccir": "Numero do Certificado",
                "ibama": "Numero da Certidão, Nome Completo, Data de expedição (dd/mm/aaaa)",
                "art": "Numero do TRT, Nome do Tecnico, Titulo Profissional do Tecnico, Registro CFTA do Tecnico",
                "planta_terreno": "Área do Terreno (Numero e Por Extenso), Perimetro do Terreno (numero e por extenso), Nome do Proprietario do Terreno ao Norte (Se nenhum, N/A), Nome do Proprietario do Terreno ao Sul (Se nenhum, N/A), Nome do Proprietario do Terreno ao Leste (Se nenhum, N/A), Nome do Proprietario do Terreno ao Oeste (Se nenhum, N/A)"
            }
            
            prompt = prompts.get(cert_type, "")
            extracted = extract_data_with_gemini(text, prompt)
            
            # Property-level certificates (no vendedor index) and conditional certificates
            if cert_type in ["itr", "ccir", "art", "planta_terreno"]:
                # Store without vendedor index
                session["certidoes"][cert_type] = extracted
                app.logger.info(f"DEBUG: Property certificate {cert_type} extracted fields: {list(extracted.keys())}")
                app.logger.info(f"DEBUG: Property certificate {cert_type} extracted data: {extracted}")
            else:
                # Per-vendedor certificates (existing logic)
                session["certidoes"][f"{cert_type}_{vendedor_idx}"] = extracted
                app.logger.info(f"DEBUG: Certificate {cert_type}_{vendedor_idx} extracted fields: {list(extracted.keys())}")
                app.logger.info(f"DEBUG: Certificate {cert_type}_{vendedor_idx} extracted data: {extracted}")
            
            # Route to appropriate flow for next step
            if session.get('is_rural'):
                session["current_step"] = get_next_rural_certificate_step(session)
            else:
                session["current_step"] = determine_next_step(session, response)
        
        # Final data collection
        elif current_step == "valor_imovel":
            session["valor"] = response
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "forma_pagamento":
            session["forma_pagamento"] = response
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "meio_pagamento":
            session["meio_pagamento"] = response
            session["current_step"] = determine_next_step(session, response)
        
        # Condominio processing (from working version)
        elif current_step == "condominio_option":
            if response == "Usar Dispensa":
                session["certidoes"]["condominio"] = {"dispensa": True}
            session["current_step"] = determine_next_step(session, response)
        
        elif current_step == "condominio_upload":
            if not file:
                return jsonify({"error": "Arquivo não fornecido"}), 400
            
            content = file.read()
            text = extract_text_from_file(content, file.filename)
            prompt = "Data do documento (dd/mm/aaaa), Nome Completo do Síndico"
            extracted = extract_data_with_gemini(text, prompt)
            
            session["certidoes"]["condominio"] = extracted
            session["current_step"] = determine_next_step(session, response)
        
        # Return next step
        return jsonify(get_next_step(session))
        
    except Exception as e:
        return jsonify({
            "session_id": session_id if 'session_id' in locals() else None,
            "status": "error",
            "message": f"Erro no processamento: {str(e)}"
        })

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Legal Document Processor",
        "version": "2.0.0",
        "framework": "Flask"
    })

# Session cleanup endpoint (optional)
@app.route('/session/<session_id>', methods=['DELETE'])
def cancel_session(session_id):
    """Cancel and delete a session"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    del sessions[session_id]
    return jsonify({"message": "Session cancelled successfully"})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Authentication endpoints

app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Use the authentication module
        user = authenticate_user(username, password)
        if user:
            session['user'] = user['username']
            session['authenticated'] = True
            session['user_data'] = user
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {"username": username}
            })
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.pop('user', None)
    session.pop('authenticated', None)
    return jsonify({"success": True, "message": "Logout successful"})

@app.route('/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    authenticated = session.get('authenticated', False)
    user = session.get('user')
    
    if authenticated and user:
        return jsonify({
            "authenticated": True,
            "user": {"username": user}
        })
    else:
        return jsonify({"authenticated": False, "user": None})

# Note: Cartório configuration is now handled by database.py module
# In-memory storage replaced with SQLite database for persistence

@app.route('/cartorio/config', methods=['GET'])
def get_cartorio_config_endpoint():
    """Get cartório configuration for authenticated user"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401
        
        # Get config from database
        config = get_cartorio_config(user_id)
        if not config:
            # Return default configuration if none found
            config = {
                'distrito': 'Campo Grande / Jardim América',
                'municipio': 'Cariacica',
                'comarca': 'Vitória',
                'estado': 'Espírito Santo',
                'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
                'quem_assina': 'Tabeliã'
            }
        
        return jsonify({
            "success": True,
            "config": config,
            "user_id": user_id
        })
            
    except Exception as e:
        return jsonify({"error": f"Config fetch error: {str(e)}"}), 500

@app.route('/cartorio/config', methods=['POST'])
def update_cartorio_config_endpoint():
    """Update cartório configuration for authenticated user"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['distrito', 'municipio', 'comarca', 'estado', 'endereco', 'quem_assina']
        for field in required_fields:
            if not data.get(field) or not data[field].strip():
                return jsonify({"error": f"{field} é obrigatório"}), 400
        
        # Validate gender concordance
        is_valid, error_message = validate_gender_concordance(data['quem_assina'])
        if not is_valid:
            return jsonify({"error": f"Invalid signatory: {error_message}"}), 400
        
        # Update configuration in database
        success = update_cartorio_config(data, user_id)
        if not success:
            return jsonify({"error": "Failed to update configuration in database"}), 500
        
        return jsonify({
            "success": True,
            "message": f"Configuration updated successfully for {user_id}",
            "user_id": user_id
        })
            
    except Exception as e:
        return jsonify({"error": f"Config update error: {str(e)}"}), 500

@app.route('/cartorio/test', methods=['GET'])
def test_cartorio_system():
    """Test cartório system configuration"""
    try:
        if not session.get('authenticated'):
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = session.get('user')
        if not user_id:
            return jsonify({"error": "User not found in session"}), 401
        
        # Get current config from database
        config = get_cartorio_config(user_id)
        if not config:
            config = {
                'distrito': 'Campo Grande / Jardim América',
                'municipio': 'Cariacica',
                'comarca': 'Vitória',
                'estado': 'Espírito Santo',
                'endereco': 'Avenida Campo Grande, nº. 432, Campo Grande, Cariacica/ES',
                'quem_assina': 'Tabeliã'
            }
        
        # Run basic tests
        tests = {
            "config_exists": bool(config),
            "all_fields_filled": all(config.get(field) for field in ['distrito', 'municipio', 'comarca', 'estado', 'endereco', 'quem_assina']),
            "api_connection": True,  # Always true since we're responding
            "user_authenticated": True
        }
        
        return jsonify({
            "success": True,
            "tests": tests,
            "config": config,
            "user_id": user_id
        })
            
    except Exception as e:
        return jsonify({"error": f"System test error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
