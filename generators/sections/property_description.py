"""Rural property description builders"""
from typing import Dict, Any
from utils.text_formatter import spell_out_area


def build_rural_property_description(session: Dict[str, Any]) -> str:
    """Build standard rural property description"""
    onus = session.get('certidoes', {}).get('onus', {})

    location = onus.get('Localização do imóvel rural', 'LOCALIZAÇÃO')
    city = onus.get('Município do imóvel', 'MUNICÍPIO')
    area_total = onus.get('Área total em m²', '0')
    north_owner = onus.get('Nome do proprietário ao Norte', 'N/A')
    south_owner = onus.get('Nome do proprietário ao Sul', 'N/A')
    east_owner = onus.get('Nome do proprietário ao Leste', 'N/A')
    west_owner = onus.get('Nome do proprietário ao Oeste', 'N/A')
    property_name = onus.get('Nome da propriedade (ex: Sítio da Vitória)', 'PROPRIEDADE')

    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    registration_number = onus.get('Número da Matrícula do Registro', 'MATRÍCULA')
    book_number = onus.get('Número do Livro', 'LIVRO')

    itr = session.get('certidoes', {}).get('itr', {})
    ccir = session.get('certidoes', {}).get('ccir', {})

    cib_number = itr.get('Numero do CIB', 'CIB_NUMBER')
    ccir_number = ccir.get('Numero do Certificado', 'CCIR_NUMBER')

    area_written = spell_out_area(area_total)

    property_description = f"""1- DA COMPRA E VENDA: E, perante mim [QUEM_ASSINA], pelo Outorgante Vendedor me foi dito que é senhor, legítimo possuidor e vende o imóvel seguinte: 1.1- Um terreno rural, situado em {location}, Município de {city}-ES, medindo a área total de {area_total} m² ({area_written}), confrontando-se ao Norte com imóvel pertencente a {north_owner}, ao Sul com imóvel pertencente a {south_owner}, a Leste com imóveis pertencentes a {east_owner}, e ao Oeste com imóvel pertencente a {west_owner}. Imóvel este cadastrado no INCRA sob o nº {cib_number}, módulo fiscal de [FISCAL_MODULE] ha, nº módulos fiscais de [NUM_MODULES], e a Fração Mínima de Parcelamento (FMP) de [FMP] ha; inscrito na Receita Federal sob o CIB nº {cib_number}, sob a denominação de "{property_name}". Matriculado no Cartório do {office_number}º Ofício da Comarca de [COMARCA]-ES sob a matrícula nº {registration_number}, pág [PAGE] do Livro nº {book_number};"""

    return property_description


def build_rural_desmembramento_description(session: Dict[str, Any]) -> str:
    """Build rural property description with desmembramento"""
    onus = session.get('certidoes', {}).get('onus', {})

    location = onus.get('Localização do imóvel rural', 'LOCALIZAÇÃO')
    city = onus.get('Município do imóvel', 'MUNICÍPIO')
    original_area = onus.get('Área total em m²', '0')
    north_owner = onus.get('Nome do proprietário ao Norte', 'N/A')
    south_owner = onus.get('Nome do proprietário ao Sul', 'N/A')
    east_owner = onus.get('Nome do proprietário ao Leste', 'N/A')
    west_owner = onus.get('Nome do proprietário ao Oeste', 'N/A')
    property_name = onus.get('Nome da propriedade (ex: Sítio da Vitória)', 'PROPRIEDADE')

    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    registration_number = onus.get('Número da Matrícula do Registro', 'MATRÍCULA')
    book_number = onus.get('Número do Livro', 'LIVRO')

    planta = session.get('certidoes', {}).get('planta_terreno', {})
    subdivided_area = planta.get('Área do Terreno (Numero e Por Extenso)', '0')
    perimeter = planta.get('Perimetro do Terreno (numero e por extenso)', '0')
    planta_north = planta.get('Nome do Proprietario do Terreno ao Norte (Se nenhum, N/A)', north_owner)
    planta_south = planta.get('Nome do Proprietario do Terreno ao Sul (Se nenhum, N/A)', south_owner)
    planta_east = planta.get('Nome do Proprietario do Terreno ao Leste (Se nenhum, N/A)', east_owner)
    planta_west = planta.get('Nome do Proprietario do Terreno ao Oeste (Se nenhum, N/A)', west_owner)

    art = session.get('certidoes', {}).get('art', {})
    technician_title = art.get('Titulo Profissional do Tecnico', 'Engenheiro Agrônomo')
    technician_name = art.get('Nome do Tecnico', 'TÉCNICO RESPONSÁVEL')
    cfta_registration = art.get('Registro CFTA do Tecnico', 'CFTA_REG')
    trt_number = art.get('Numero do TRT', 'TRT_NUMBER')

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

    area_written = spell_out_area(subdivided_area.split(' ')[0] if isinstance(subdivided_area, str) else str(subdivided_area))
    original_area_written = spell_out_area(original_area)
    remaining_area_written = spell_out_area(remaining_area)
    perimeter_written = spell_out_area(perimeter.split(' ')[0] if isinstance(perimeter, str) else str(perimeter))

    property_description = f"""1- DA COMPRA E VENDA: E, perante mim [QUEM_ASSINA], pelo Outorgante Vendedor me foi dito que é senhor, legítimo possuidor e vende o imóvel seguinte: 1.1- Um terreno rural e legitimado, situado em {location}, Município de {city}-ES, medindo a área de {subdivided_area} m² ({area_written}) e perímetro de {perimeter} m ({perimeter_written}), confrontando-se ao Norte com imóvel pertencente a {planta_north}, ao Sul com imóvel pertencente a {planta_south}, a Leste com imóveis pertencentes a {planta_east}, e a Oeste com imóvel pertencente a {planta_west}; descrito topograficamente e caracterizado na planta e no memorial descritivo, realizados pelo {technician_title}, o Sr. {technician_name}, Registro CFTA: {cfta_registration}, planta datada de [PLAN_DATE], com Termo de Responsabilidade Técnica (TRT) sob o nº {trt_number}. Imóvel este que será desmembrado do terreno original, medindo a área total de {original_area} m² ({original_area_written}), confrontando-se ao Norte com imóvel pertencente a {north_owner}, ao Sul com imóvel pertencente a {south_owner}, a Leste com imóveis pertencentes a {east_owner} e ao Oeste com imóveis pertencentes a {west_owner}. Imóvel este cadastrado no INCRA sob o nº {cib_number}, módulo fiscal de [FISCAL_MODULE] ha, nº módulos fiscais de [NUM_MODULES], e a Fração Mínima de Parcelamento (FMP) de [FMP] ha; inscrito na Receita Federal sob o CIB nº {cib_number}, sob a denominação de "{property_name}". Matriculado no Cartório do {office_number}º Ofício da Comarca de [COMARCA]-ES sob a matrícula nº {registration_number}, pág [PAGE] do Livro nº {book_number}; 1.1.1 - restando para o Outorgante Vendedor a área remanescente total de {remaining_area} m² ({remaining_area_written}), confrontando-se por seus diversos lados com quem de direito."""

    return property_description
