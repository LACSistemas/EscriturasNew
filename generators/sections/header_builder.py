"""Header builders for escrituras"""
from typing import Dict, Any
from generators.sections.parties_formatter import extract_party_names


def build_rural_header(session: Dict[str, Any]) -> str:
    """Build the escritura header with OUTORGANTE/OUTORGADO terminology"""
    vendedores = session.get("vendedores", [])
    compradores = session.get("compradores", [])

    vendedor_names = extract_party_names(vendedores, "vendedor")
    comprador_names = extract_party_names(compradores, "comprador")

    if len(vendedores) == 1:
        vendedor_title = "OUTORGANTE VENDEDOR"
    else:
        vendedor_title = "OUTORGANTES VENDEDORES"

    if len(compradores) == 1:
        comprador_title = "OUTORGADO COMPRADOR"
    else:
        comprador_title = "OUTORGADOS COMPRADORES"

    header = f"""ESCRITURA PÚBLICA DE COMPRA E VENDA QUE FAZ COMO {vendedor_title} {vendedor_names}, E COMO {comprador_title} {comprador_names}, NA FORMA ABAIXO:"""

    return header
