"""Certificate workflow management"""
from typing import Dict, Any


def get_next_certificate_step(session: Dict[str, Any]) -> str:
    """Determine next certificate to collect"""
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

    # Safety check
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
        # Check if we need to collect condominio declaration for Apto
        if session.get("tipo_escritura") == "Escritura de Apto" and "condominio_processed" not in session["temp_data"]:
            session["temp_data"]["condominio_processed"] = True
            return "condominio_option"
        else:
            return "valor_imovel"


def get_next_rural_certificate_step(session: Dict[str, Any]) -> str:
    """Determine next certificate to collect for rural escrituras"""
    # Rural certificate order: PER-VENDOR ONLY
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
