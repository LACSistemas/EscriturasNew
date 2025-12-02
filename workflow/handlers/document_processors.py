"""Document processors for FileUploadHandler - OCR + AI extraction"""
from typing import Dict, Any
from services.ocr_service_async import extract_text_from_file_async
from services.ai_service_async import extract_data_with_gemini_async
from models.session import set_current_comprador, set_current_vendedor, get_current_comprador, get_current_vendedor, add_certidao_to_session, ensure_temp_data
from utils.validators import sanitize_extracted_data


async def process_documento_comprador(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process comprador document (RG, CNH, or CTPS)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # Extract text with OCR
    text = await extract_text_from_file_async(file_data, filename, vision_client)

    # Determine prompt based on document type
    temp_data = ensure_temp_data(session)
    doc_type = temp_data.get("documento_tipo", "")

    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    else:  # Carteira de Trabalho
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

    # Extract data with AI
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)

    # Build comprador data
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
    else:  # CTPS
        comprador["ctps_serie"] = extracted.get("Série da Carteira", "")
        comprador["ctps_numero"] = extracted.get("Número da Carteira", "")
        comprador["sexo"] = extracted.get("Gênero", "")

    # Store using helper
    set_current_comprador(session, comprador)
    return comprador


async def process_empresa_comprador(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process comprador empresa document (CNPJ) - empresa data only"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Razão Social, 2: CNPJ, 3: Endereço completo"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)

    comprador = {
        "tipo": "Pessoa Jurídica",
        "razao_social": extracted.get("Razão Social", ""),
        "cnpj": extracted.get("CNPJ", ""),
        "endereco": extracted.get("Endereço completo", "")
    }

    # Store using helper
    set_current_comprador(session, comprador)
    return comprador


async def process_representante_comprador(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process legal representative document for empresa comprador"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # Get document type from temp_data
    temp_data = ensure_temp_data(session)
    doc_type = temp_data.get("documento_tipo", "Carteira de Identidade")

    # Extract text from document
    text = await extract_text_from_file_async(file_data, filename, vision_client)

    # Dynamic prompt based on document type
    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Número do CPF, 3: Data de Nascimento, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Número da CNH, 3: Órgão de Expedição da CNH, 4: Data de Nascimento, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    else:  # Carteira de Trabalho
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

    # Extract data with AI
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    extracted = sanitize_extracted_data(extracted)

    # Get current comprador (empresa) data
    current_comprador = get_current_comprador(session)

    # Add representative data to comprador
    representante_data = {
        "nome_completo": extracted.get("Nome Completo", ""),
        "data_nascimento": extracted.get("Data de Nascimento", ""),
        "documento_tipo": doc_type,
        "sexo": extracted.get("Gênero", "")
    }

    if doc_type == "Carteira de Identidade":
        representante_data["cpf"] = extracted.get("Número do CPF", "")
    elif doc_type == "CNH":
        representante_data["cnh_numero"] = extracted.get("Número da CNH", "")
        representante_data["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
    else:  # CTPS
        representante_data["ctps_serie"] = extracted.get("Série da Carteira", "")
        representante_data["ctps_numero"] = extracted.get("Número da Carteira", "")

    # Add representante to empresa data
    current_comprador["representante_legal"] = representante_data
    set_current_comprador(session, current_comprador)

    return representante_data


async def process_certidao_casamento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de casamento"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome Completo do Cônjuge, 2: Data do Casamento, 3: Regime de Bens, 4: Cartório de Registro"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    certidao_data = {
        "nome_conjuge": extracted.get("Nome Completo do Cônjuge", ""),
        "data_casamento": extracted.get("Data do Casamento", ""),
        "regime_bens": extracted.get("Regime de Bens", ""),
        "cartorio": extracted.get("Cartório de Registro", "")
    }

    # Store using helper
    temp_data = ensure_temp_data(session)
    if "current_comprador" in temp_data and temp_data["current_comprador"]:
        temp_data["current_comprador"]["certidao_casamento"] = certidao_data

    return certidao_data


async def process_certidao_nascimento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de nascimento (for solteiros)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Pai (nome completo), 2: Nome da Mãe (nome completo)"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)

    certidao_data = {
        "nome_pai": extracted.get("Nome do Pai", ""),
        "nome_mae": extracted.get("Nome da Mãe", "")
    }

    # Store in current comprador/vendedor
    temp_data = ensure_temp_data(session)
    if "current_comprador" in temp_data and temp_data["current_comprador"]:
        temp_data["current_comprador"]["certidao_nascimento"] = certidao_data
    elif "current_vendedor" in temp_data and temp_data["current_vendedor"]:
        temp_data["current_vendedor"]["certidao_nascimento"] = certidao_data

    return certidao_data


async def process_documento_conjuge(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process cônjuge document"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)

    doc_type = session.get("temp_data", {}).get("conjuge_doc_tipo", "Carteira de Identidade")

    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero"
    else:  # CTPS
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero"

    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    conjuge_data = {
        "nome_completo": extracted.get("Nome Completo", ""),
        "data_nascimento": extracted.get("Data de Nascimento", ""),
        "documento_tipo": doc_type,
        "sexo": extracted.get("Gênero", "")
    }

    if doc_type == "Carteira de Identidade":
        conjuge_data["cpf"] = extracted.get("Número do CPF", "")
    elif doc_type == "CNH":
        conjuge_data["cnh_numero"] = extracted.get("Número da CNH", "")
        conjuge_data["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
    else:
        conjuge_data["ctps_serie"] = extracted.get("Série da Carteira", "")
        conjuge_data["ctps_numero"] = extracted.get("Número da Carteira", "")

    # Store using helper
    temp_data = ensure_temp_data(session)
    if "current_comprador" in temp_data and temp_data["current_comprador"]:
        temp_data["current_comprador"]["conjuge_data"] = conjuge_data

    return conjuge_data


# ============================================================================
# VENDEDOR PROCESSORS
# ============================================================================

async def process_documento_vendedor(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process vendedor document (similar to comprador)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    doc_type = session.get("temp_data", {}).get("documento_tipo", "")

    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero"
    else:
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero"

    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    vendedor = {
        "tipo": "Pessoa Física",
        "nome_completo": extracted.get("Nome Completo", ""),
        "data_nascimento": extracted.get("Data de Nascimento", ""),
        "documento_tipo": doc_type,
        "sexo": extracted.get("Gênero", "")
    }

    if doc_type == "Carteira de Identidade":
        vendedor["cpf"] = extracted.get("Número do CPF", "")
    elif doc_type == "CNH":
        vendedor["cnh_numero"] = extracted.get("Número da CNH", "")
        vendedor["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
    else:
        vendedor["ctps_serie"] = extracted.get("Série da Carteira", "")
        vendedor["ctps_numero"] = extracted.get("Número da Carteira", "")

    # Store using helper
    set_current_vendedor(session, vendedor)
    return vendedor


async def process_empresa_vendedor(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process vendedor empresa document - empresa data only"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Razão Social, 2: CNPJ, 3: Endereço completo"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)

    vendedor = {
        "tipo": "Pessoa Jurídica",
        "razao_social": extracted.get("Razão Social", ""),
        "cnpj": extracted.get("CNPJ", ""),
        "endereco": extracted.get("Endereço completo", "")
    }

    # Store using helper
    set_current_vendedor(session, vendedor)
    return vendedor


async def process_representante_vendedor(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process legal representative document for empresa vendedor"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # Get document type from temp_data
    temp_data = ensure_temp_data(session)
    doc_type = temp_data.get("documento_tipo", "Carteira de Identidade")

    # Extract text from document
    text = await extract_text_from_file_async(file_data, filename, vision_client)

    # Dynamic prompt based on document type
    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Número do CPF, 3: Data de Nascimento, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Número da CNH, 3: Órgão de Expedição da CNH, 4: Data de Nascimento, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    else:  # Carteira de Trabalho
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

    # Extract data with AI
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    extracted = sanitize_extracted_data(extracted)

    # Get current vendedor (empresa) data
    current_vendedor = get_current_vendedor(session)

    # Add representative data to vendedor
    representante_data = {
        "nome_completo": extracted.get("Nome Completo", ""),
        "data_nascimento": extracted.get("Data de Nascimento", ""),
        "documento_tipo": doc_type,
        "sexo": extracted.get("Gênero", "")
    }

    if doc_type == "Carteira de Identidade":
        representante_data["cpf"] = extracted.get("Número do CPF", "")
    elif doc_type == "CNH":
        representante_data["cnh_numero"] = extracted.get("Número da CNH", "")
        representante_data["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição da CNH", "")
    else:  # CTPS
        representante_data["ctps_serie"] = extracted.get("Série da Carteira", "")
        representante_data["ctps_numero"] = extracted.get("Número da Carteira", "")

    # Add representante to empresa data
    current_vendedor["representante_legal"] = representante_data
    set_current_vendedor(session, current_vendedor)

    return representante_data


async def process_vendedor_conjuge_documento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process vendedor cônjuge document"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    doc_type = session.get("temp_data", {}).get("conjuge_doc_tipo", "Carteira de Identidade")

    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição, 5: Gênero"
    else:
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero"

    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    conjuge_data = {
        "nome_completo": extracted.get("Nome Completo", ""),
        "data_nascimento": extracted.get("Data de Nascimento", ""),
        "documento_tipo": doc_type,
        "sexo": extracted.get("Gênero", "")
    }

    if doc_type == "Carteira de Identidade":
        conjuge_data["cpf"] = extracted.get("Número do CPF", "")
    elif doc_type == "CNH":
        conjuge_data["cnh_numero"] = extracted.get("Número da CNH", "")
        conjuge_data["cnh_orgao_expedidor"] = extracted.get("Órgão de Expedição", "")
    else:
        conjuge_data["ctps_serie"] = extracted.get("Série da Carteira", "")
        conjuge_data["ctps_numero"] = extracted.get("Número da Carteira", "")

    # Store using helper
    temp_data = ensure_temp_data(session)
    if "current_vendedor" in temp_data and temp_data["current_vendedor"]:
        temp_data["current_vendedor"]["conjuge_data"] = conjuge_data

    return conjuge_data


# ============================================================================
# GENERIC CERTIDÃO PROCESSOR (DRY)
# ============================================================================

async def process_certidao_generic(
    file_data: bytes,
    filename: str,
    session: Dict[str, Any],
    tipo: str,
    prompt: str,
    field_mapping: dict,
    vendedor_specific: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Generic certificate processor - DRY pattern

    Args:
        tipo: Certificate type (e.g., "negativa_federal")
        prompt: AI extraction prompt
        field_mapping: Map of extracted fields to certidao fields
        vendedor_specific: True if certidão is tied to specific vendedor
    """
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # Extract text with OCR
    text = await extract_text_from_file_async(file_data, filename, vision_client)

    # Extract data with AI
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)

    # Build certidao using field mapping
    certidao = {"tipo": tipo, "dispensada": False}
    for extract_key, certidao_key in field_mapping.items():
        certidao[certidao_key] = extracted.get(extract_key, "")

    # Get vendedor index if needed
    vendedor_index = None
    if vendedor_specific:
        temp_data = ensure_temp_data(session)
        vendedor_index = temp_data.get("current_vendedor_index", 0)
        certidao["vendedor_index"] = vendedor_index

    # Store using helper
    add_certidao_to_session(session, tipo, certidao, vendedor_index=vendedor_index)
    return certidao


# ============================================================================
# CERTIDÃO PROCESSORS
# ============================================================================

async def process_certidao_onus(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de ônus reais"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Data de Emissão, 2: Validade, 3: Matrícula do Imóvel, 4: Possui Ônus? (Sim/Não), 5: Descrição dos Ônus (se houver)"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    certidao = {
        "tipo": "onus",
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "matricula": extracted.get("Matrícula do Imóvel", ""),
        "possui_onus": extracted.get("Possui Ônus?", "Não"),
        "descricao_onus": extracted.get("Descrição dos Ônus (se houver)", "")
    }

    # Store using helper
    add_certidao_to_session(session, "onus", certidao, dispensada=False)
    return certidao


async def process_certidao_negativa_federal(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa federal"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    temp_data = ensure_temp_data(session)
    vendedor_index = temp_data.get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_federal",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    # Store using helper
    add_certidao_to_session(session, "negativa_federal", certidao, vendedor_index=vendedor_index)
    return certidao


async def process_certidao_negativa_estadual(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa estadual"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    temp_data = ensure_temp_data(session)
    vendedor_index = temp_data.get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_estadual",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    add_certidao_to_session(session, "negativa_estadual", certidao, vendedor_index=vendedor_index)
    return certidao


async def process_certidao_negativa_municipal(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa municipal"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    temp_data = ensure_temp_data(session)
    vendedor_index = temp_data.get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_municipal",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    add_certidao_to_session(session, "negativa_municipal", certidao, vendedor_index=vendedor_index)
    return certidao


async def process_certidao_negativa_trabalhista(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa trabalhista"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    temp_data = ensure_temp_data(session)
    vendedor_index = temp_data.get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_trabalhista",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    add_certidao_to_session(session, "negativa_trabalhista", certidao, vendedor_index=vendedor_index)
    return certidao


# ============================================================================
# ADDITIONAL URBAN CERTIDÕES (using generic processor)
# ============================================================================

async def process_certidao_condominio(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de condomínio (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="condominio",
        prompt="1: Número da Matrícula, 2: Data de Emissão, 3: Débitos Pendentes (Sim/Não), 4: Valor dos Débitos (se houver)",
        field_mapping={
            "Número da Matrícula": "matricula",
            "Data de Emissão": "data_emissao",
            "Débitos Pendentes (Sim/Não)": "possui_debitos",
            "Valor dos Débitos (se houver)": "valor_debitos"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_iptu(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de IPTU - Imposto Predial e Territorial Urbano (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="iptu",
        prompt="1: Inscrição Imobiliária, 2: Endereço do Imóvel, 3: Último Ano Pago, 4: Débitos Pendentes (Sim/Não), 5: Valor dos Débitos (se houver)",
        field_mapping={
            "Inscrição Imobiliária": "inscricao_imobiliaria",
            "Endereço do Imóvel": "endereco",
            "Último Ano Pago": "ultimo_ano_pago",
            "Débitos Pendentes (Sim/Não)": "possui_debitos",
            "Valor dos Débitos (se houver)": "valor_debitos"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_matricula(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process matrícula do imóvel (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="matricula",
        prompt="1: Número da Matrícula, 2: Cartório de Registro, 3: Proprietário Atual, 4: Área do Imóvel, 5: Endereço Completo",
        field_mapping={
            "Número da Matrícula": "numero_matricula",
            "Cartório de Registro": "cartorio",
            "Proprietário Atual": "proprietario",
            "Área do Imóvel": "area",
            "Endereço Completo": "endereco"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_objeto_pe(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de objeto e pé - para apartamentos (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="objeto_pe",
        prompt="1: Número da Matrícula, 2: Unidade/Apartamento, 3: Bloco/Torre, 4: Data de Emissão, 5: Validade",
        field_mapping={
            "Número da Matrícula": "matricula",
            "Unidade/Apartamento": "unidade",
            "Bloco/Torre": "bloco",
            "Data de Emissão": "data_emissao",
            "Validade": "validade"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_indisponibilidade(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de indisponibilidade de bens (vendedor-specific)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="indisponibilidade",
        prompt="1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade, 5: Possui Indisponibilidade (Sim/Não)",
        field_mapping={
            "Nome do Titular": "titular",
            "CPF/CNPJ": "cpf_cnpj",
            "Data de Emissão": "data_emissao",
            "Validade": "validade",
            "Possui Indisponibilidade (Sim/Não)": "possui_indisponibilidade"
        },
        vendedor_specific=True,
        **kwargs
    )


async def process_certidao_distribuidora(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão distribuidora (vendedor-specific)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="distribuidora",
        prompt="1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade, 5: Possui Ações (Sim/Não)",
        field_mapping={
            "Nome do Titular": "titular",
            "CPF/CNPJ": "cpf_cnpj",
            "Data de Emissão": "data_emissao",
            "Validade": "validade",
            "Possui Ações (Sim/Não)": "possui_acoes"
        },
        vendedor_specific=True,
        **kwargs
    )


# ============================================================================
# RURAL CERTIDÕES (using generic processor)
# ============================================================================

async def process_certidao_itr(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process ITR - Imposto Territorial Rural (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="itr",
        prompt="1: NIRF, 2: Área Total (hectares), 3: Último Ano Pago, 4: Débitos Pendentes (Sim/Não)",
        field_mapping={
            "NIRF": "nirf",
            "Área Total (hectares)": "area_total",
            "Último Ano Pago": "ultimo_ano_pago",
            "Débitos Pendentes (Sim/Não)": "possui_debitos"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_ccir(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process CCIR - Certificado de Cadastro de Imóvel Rural (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="ccir",
        prompt="1: Código CCIR, 2: NIRF, 3: Área Total (hectares), 4: Data de Emissão, 5: Situação (Regular/Irregular)",
        field_mapping={
            "Código CCIR": "codigo_ccir",
            "NIRF": "nirf",
            "Área Total (hectares)": "area_total",
            "Data de Emissão": "data_emissao",
            "Situação (Regular/Irregular)": "situacao"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_incra(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa INCRA (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="incra",
        prompt="1: NIRF, 2: Data de Emissão, 3: Validade, 4: Débitos (Sim/Não)",
        field_mapping={
            "NIRF": "nirf",
            "Data de Emissão": "data_emissao",
            "Validade": "validade",
            "Débitos (Sim/Não)": "possui_debitos"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_certidao_ibama(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa IBAMA (property-level)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="ibama",
        prompt="1: Proprietário, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade, 5: Infrações (Sim/Não)",
        field_mapping={
            "Proprietário": "proprietario",
            "CPF/CNPJ": "cpf_cnpj",
            "Data de Emissão": "data_emissao",
            "Validade": "validade",
            "Infrações (Sim/Não)": "possui_infracoes"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_art_desmembramento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process ART de desmembramento (for rural desmembramento)"""
    return await process_certidao_generic(
        file_data, filename, session,
        tipo="art_desmembramento",
        prompt="1: Número ART, 2: Responsável Técnico, 3: CREA, 4: Data de Emissão, 5: Área Total Desmembrada (hectares)",
        field_mapping={
            "Número ART": "numero_art",
            "Responsável Técnico": "responsavel_tecnico",
            "CREA": "crea",
            "Data de Emissão": "data_emissao",
            "Área Total Desmembrada (hectares)": "area_desmembrada"
        },
        vendedor_specific=False,
        **kwargs
    )


async def process_planta_desmembramento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process planta de desmembramento (for rural desmembramento)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # For planta, we just extract basic info
    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Área do Lote (hectares), 2: Confrontações/Divisas, 3: Número do Lote, 4: Responsável Técnico"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)
    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)


    # Sanitize and validate extracted data
    extracted = sanitize_extracted_data(extracted)
    certidao = {
        "tipo": "planta_desmembramento",
        "area_lote": extracted.get("Área do Lote (hectares)", ""),
        "confrontacoes": extracted.get("Confrontações/Divisas", ""),
        "numero_lote": extracted.get("Número do Lote", ""),
        "responsavel_tecnico": extracted.get("Responsável Técnico", ""),
        "dispensada": False
    }

    add_certidao_to_session(session, "planta_desmembramento", certidao, dispensada=False)
    return certidao
