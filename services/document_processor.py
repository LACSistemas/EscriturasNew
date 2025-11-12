"""Document processing service"""
import logging
from typing import Dict, Any
from utils.helpers import ensure_temp_data_saved

logger = logging.getLogger(__name__)


def process_all_documents(session: Dict[str, Any], generate_escritura_fn) -> Dict[str, Any]:
    """Process all collected documents and generate the deed"""
    logger.info("DEBUG: Processing final documents...")
    logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    logger.info(f"DEBUG: temp_data = {session.get('temp_data', {})}")

    # Ensure any remaining temp data gets saved
    ensure_temp_data_saved(session)

    logger.info(f"DEBUG: After saving temp data:")
    logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")

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
    escritura = generate_escritura_fn(session)

    return {
        "extracted_data": all_data,
        "escritura": escritura
    }


def process_all_rural_documents(session: Dict[str, Any], generate_rural_escritura_fn) -> Dict[str, Any]:
    """Process all collected documents and generate the rural escritura"""
    logger.info("DEBUG: Processing final rural documents...")
    logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")
    logger.info(f"DEBUG: rural type = {session.get('tipo_escritura_rural', 'unknown')}")
    logger.info(f"DEBUG: temp_data = {session.get('temp_data', {})}")

    # Ensure any remaining temp data gets saved
    ensure_temp_data_saved(session)

    logger.info(f"DEBUG: After saving temp data:")
    logger.info(f"DEBUG: session['compradores'] = {session.get('compradores', [])}")
    logger.info(f"DEBUG: session['vendedores'] = {session.get('vendedores', [])}")

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
    escritura = generate_rural_escritura_fn(session)

    return {
        "extracted_data": all_data,
        "escritura": escritura
    }
