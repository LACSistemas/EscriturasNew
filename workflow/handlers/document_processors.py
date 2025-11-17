"""Document processors for FileUploadHandler - OCR + AI extraction"""
from typing import Dict, Any
from services.ocr_service_async import extract_text_from_file_async
from services.ai_service_async import extract_data_with_gemini_async


async def process_documento_comprador(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process comprador document (RG, CNH, or CTPS)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    # Extract text with OCR
    text = await extract_text_from_file_async(file_data, filename, vision_client)

    # Determine prompt based on document type
    doc_type = session.get("temp_data", {}).get("documento_tipo", "")

    if doc_type == "Carteira de Identidade":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número do CPF, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    elif doc_type == "CNH":
        prompt = "1: Nome Completo, 2: Data de Nascimento, 3: Número da CNH, 4: Órgão de Expedição da CNH, 5: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"
    else:  # Carteira de Trabalho
        prompt = "1: Nome Completo, 2: Série da Carteira, 3: Número da Carteira, 4: Gênero (analise o primeiro nome e determine se é tipicamente Masculino ou Feminino baseado em nomes brasileiros típicos. Considere nomes como João, Carlos, Pedro, Lucas, Rafael = Masculino; Maria, Ana, Carla, Cecilia, Fernanda = Feminino. Se incerto, use Masculino)"

    # Extract data with AI
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

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

    # Store in temp_data
    session.setdefault("temp_data", {})["current_comprador"] = comprador

    return comprador


async def process_empresa_comprador(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process comprador empresa document (CNPJ)"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Razão Social, 2: CNPJ, 3: Endereço completo, 4: Nome do Representante Legal"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    comprador = {
        "tipo": "Pessoa Jurídica",
        "razao_social": extracted.get("Razão Social", ""),
        "cnpj": extracted.get("CNPJ", ""),
        "endereco": extracted.get("Endereço completo", ""),
        "representante_legal": extracted.get("Nome do Representante Legal", "")
    }

    session.setdefault("temp_data", {})["current_comprador"] = comprador
    return comprador


async def process_certidao_casamento(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão de casamento"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome Completo do Cônjuge, 2: Data do Casamento, 3: Regime de Bens, 4: Cartório de Registro"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    certidao_data = {
        "nome_conjuge": extracted.get("Nome Completo do Cônjuge", ""),
        "data_casamento": extracted.get("Data do Casamento", ""),
        "regime_bens": extracted.get("Regime de Bens", ""),
        "cartorio": extracted.get("Cartório de Registro", "")
    }

    # Store in current_comprador
    if "current_comprador" in session.get("temp_data", {}):
        session["temp_data"]["current_comprador"]["certidao_casamento"] = certidao_data

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

    # Store in current_comprador
    if "current_comprador" in session.get("temp_data", {}):
        session["temp_data"]["current_comprador"]["conjuge_data"] = conjuge_data

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

    session.setdefault("temp_data", {})["current_vendedor"] = vendedor
    return vendedor


async def process_empresa_vendedor(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process vendedor empresa document"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Razão Social, 2: CNPJ, 3: Endereço completo, 4: Nome do Representante Legal"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    vendedor = {
        "tipo": "Pessoa Jurídica",
        "razao_social": extracted.get("Razão Social", ""),
        "cnpj": extracted.get("CNPJ", ""),
        "endereco": extracted.get("Endereço completo", ""),
        "representante_legal": extracted.get("Nome do Representante Legal", "")
    }

    session.setdefault("temp_data", {})["current_vendedor"] = vendedor
    return vendedor


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

    if "current_vendedor" in session.get("temp_data", {}):
        session["temp_data"]["current_vendedor"]["conjuge_data"] = conjuge_data

    return conjuge_data


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

    certidao = {
        "tipo": "onus",
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "matricula": extracted.get("Matrícula do Imóvel", ""),
        "possui_onus": extracted.get("Possui Ônus?", "Não"),
        "descricao_onus": extracted.get("Descrição dos Ônus (se houver)", "")
    }

    session.setdefault("certidoes", {})["onus"] = certidao
    return certidao


async def process_certidao_negativa_federal(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa federal"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    vendedor_index = session.get("temp_data", {}).get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_federal",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    # Store with vendedor index
    key = f"negativa_federal_{vendedor_index}"
    session.setdefault("certidoes", {})[key] = certidao
    return certidao


async def process_certidao_negativa_estadual(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa estadual"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    vendedor_index = session.get("temp_data", {}).get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_estadual",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    key = f"negativa_estadual_{vendedor_index}"
    session.setdefault("certidoes", {})[key] = certidao
    return certidao


async def process_certidao_negativa_municipal(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa municipal"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    vendedor_index = session.get("temp_data", {}).get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_municipal",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    key = f"negativa_municipal_{vendedor_index}"
    session.setdefault("certidoes", {})[key] = certidao
    return certidao


async def process_certidao_negativa_trabalhista(file_data: bytes, filename: str, session: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Process certidão negativa trabalhista"""
    vision_client = kwargs.get('vision_client')
    gemini_model = kwargs.get('gemini_model')

    text = await extract_text_from_file_async(file_data, filename, vision_client)
    prompt = "1: Nome do Titular, 2: CPF/CNPJ, 3: Data de Emissão, 4: Validade"
    extracted = await extract_data_with_gemini_async(text, prompt, gemini_model)

    vendedor_index = session.get("temp_data", {}).get("current_vendedor_index", 0)

    certidao = {
        "tipo": "negativa_trabalhista",
        "vendedor_index": vendedor_index,
        "titular": extracted.get("Nome do Titular", ""),
        "cpf_cnpj": extracted.get("CPF/CNPJ", ""),
        "data_emissao": extracted.get("Data de Emissão", ""),
        "validade": extracted.get("Validade", ""),
        "dispensada": False
    }

    key = f"negativa_trabalhista_{vendedor_index}"
    session.setdefault("certidoes", {})[key] = certidao
    return certidao
