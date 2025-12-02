"""Urban escritura generator"""
from typing import Dict, Any
from database import get_cartorio_config
from gender_concordance import (
    get_cartorio_template_data,
    build_escritura_header,
    build_escritura_authentication,
    build_escritura_declarations,
    build_escritura_final_clauses
)
from utils.gender_utils import determine_gender_suffix
from utils.date_formatter import format_date_for_deed
from generators.sections.parties_formatter import format_parties
from generators.sections.certificates_formatter import format_certificates_section


def generate_escritura_text(session: Dict[str, Any], user_id=None) -> str:
    """Generate the final urban deed text"""
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
    descricao_pagamento = session.get("descricao_pagamento", "À vista via transferência bancária/PIX")

    # Format the date
    formatted_date = format_date_for_deed()

    # Build escritura header with proper gender concordance
    header = build_escritura_header(template_data, formatted_date)

    # Build authentication section with proper gender concordance
    auth_section = build_escritura_authentication(template_data)

    # Combine header with parties information
    escritura = f"""{header} de um lado como **{vendedor_suffixes['title']}**: {vendedores_text}; e de outro lado, como **{comprador_suffixes['title']}**: {compradores_text}; {auth_section}"""

    # Get property information from Certidão de Ônus
    onus_data = session.get("certidoes", {}).get("onus", {})
    imovel_descricao = onus_data.get("Descrição breve do imóvel", "***IMOVEL***")
    oficio_numero = onus_data.get("Número do Ofício (apenas o número, ex: 1, 2, 3)", "***")
    zona_cartorio = onus_data.get("Zona do Cartório (ex: 1ª Zona, 2ª Zona)", "***")
    cidade_cartorio = onus_data.get("Cidade do Cartório", "***")
    matricula_numero = onus_data.get("Número da Matrícula do Registro", "***")
    livro_numero = onus_data.get("Número do Livro", "***")

    # Add property description and sale terms
    escritura += f""" E pel{vendedor_suffixes['article']} **{vendedor_suffixes['title']}** referid{vendedor_suffixes['article']}, foi dito que {'são' if len(session['vendedores']) > 1 else 'é'} don{vendedor_suffixes['article']}, senhor{'es' if len(session['vendedores']) > 1 else ''} e legítim{vendedor_suffixes['article']} possuid{vendedor_suffixes['possessive']}, absolutamente livre e desembaraçado de todo e qualquer ônus real, do imóvel constituído pelo: {imovel_descricao}; devidamente registrado no Cartório de Registro Geral de Imóveis do {oficio_numero}º Ofício - {zona_cartorio} - {cidade_cartorio}, matricula nº {matricula_numero} do livro nº {livro_numero}, com valor venal atribuído pela municipalidade local de ********; que assim possuindo o referido imóvel, vende ao **{comprador_suffixes['title']}**, como efetivamente vendido tem, por bem desta escritura, da cláusula CONSTITUTI, e na melhor forma de direito, pelo preço certo e ajustado de **[{valor}]**, pago ***{descricao_pagamento}***, do que desde já, lhes dá plena, rasa e geral quitação da importância recebida, para nada mais exigirem com relação a presente venda, transmitindo, como de fato ora transmite na pessoa d{comprador_suffixes['article']} **{comprador_suffixes['title']}**, todo direito, posse, domínio e ação que exerciam sobre o referido imovel, e prometendo por si e seus sucessores legítimos a presente venda, boa, firme e valiosa para sempre, obrigando-se a responderem pela evicção de direito, se chamado a autoria. Pel{comprador_suffixes['article']} **{comprador_suffixes['title']}**, me foi dito que, aceita a presente escritura como nela se contem e declara, por estar o mesmo de inteiro com o ajustado e contratado entre si e {vendedor_suffixes['article']} **{vendedor_suffixes['title']}**. Foram apresentados as seguintes certidões e foram feitas as seguintes declarações:"""

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
