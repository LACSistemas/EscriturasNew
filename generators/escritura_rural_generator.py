"""Rural escritura generator"""
from typing import Dict, Any
from database import get_cartorio_config
from gender_concordance import get_cartorio_template_data
from utils.date_formatter import format_date_for_deed
from utils.text_formatter import spell_out_currency
from generators.sections.parties_formatter import format_rural_parties
from generators.sections.certificates_formatter import format_rural_certificates_section
from generators.sections.property_description import (
    build_rural_property_description,
    build_rural_desmembramento_description
)
from generators.sections.header_builder import build_rural_header


def generate_escritura_rural_text(session: Dict[str, Any], user_id=None) -> str:
    """Generate the final rural escritura text"""
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

    # Apply defaults to parties before formatting
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
