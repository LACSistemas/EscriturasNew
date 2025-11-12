"""Certificate section formatting for escrituras"""
from typing import Dict, Any
from utils.helpers import generate_hash_code


def format_certificates_section(session: Dict[str, Any]) -> str:
    """Format the certificates section for urban deeds"""
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
        for v_idx, vendedor in enumerate(vendedores):
            vendedor_name = vendedor.get("nome_completo", f"Vendedor {v_idx + 1}")
            cert_key = f"{cert_type}_{v_idx}"

            if cert_key in certidoes:
                if certidoes[cert_key].get("dispensa"):
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
                            cert_text += f"""

**{cert_counter}º) {cert_title}** -  nº "{cert.get('Número da Certidão', '***')}"  - Certifica-se que ({cert.get('Nome Completo', '***')}), inscrita no CNPJ sob o nº "{cert.get('CPF', '***')}", NÃO CONSTA do Banco Nacional de Devedores Trabalhistas, emitida em "{cert.get('Data de Emissão (dd/mm/aaaa)', '***')}", às "{cert.get('Horário de Emissão (hh:mm)', '***')}" - válida até "{cert.get('Validade da Certidão(dd/mm/aaaa)', '***')}"" - Confirmada a sua validade na internet no endereço: www.tst.jus.br;"""
                        else:
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - nº {cert.get('Número da Certidão', '***')} - Certifica-se que {cert.get('Nome Completo', '***')}, inscrito no CPF/MF sob o nº {cert.get('CPF', '***')}, NÃO CONSTA do Banco Nacional de Devedores Trabalhistas, emitida em {cert.get('Data de Emissão (dd/mm/aaaa)', '***')} às {cert.get('Horário de Emissão (hh:mm)', '***')} hs - válida até {cert.get('Validade da Certidão(dd/mm/aaaa)', '***')} - Confirmada a sua validade na internet no endereço: www.tst.jus.br;"""
                    elif cert_type == "indisponibilidade":
                        if vendedor.get("tipo") == "Pessoa Jurídica":
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - PROVIMENTO Nº 39/2014: CNPJ pesquisado "{cert.get('CNPJ', '***')}" de *"{cert.get('Nome da Empresa', '***')}"- ME (-----------) na data : "{cert.get('Data da Consulta', '***')}" às "{cert.get('Hora da Consulta', '***')}". RESULTADO: NEGATIVO – código "{cert.get('Código HASH', '***')}" """
                        else:
                            cert_text += f"""

**{cert_counter}º) {cert_title}** - PROVIMENTO Nº 39/2014: ***** RESULTADO: **NEGATIVO.** CODIGO HASH: {cert.get('Código HASH', '***')} ;"""

                cert_counter += 1

    # Add condominium declaration only for Apto (not for Lote)
    if session.get("tipo_escritura") != "Escritura de Lote":
        condominio_data = certidoes.get("condominio", {})

        if condominio_data.get("dispensa"):
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de *****************. Ass: **************** - Síndico;"""
        elif condominio_data:
            data_documento = condominio_data.get("Data do documento (dd/mm/aaaa)", "*****************")
            nome_sindico = condominio_data.get("Nome Completo do Síndico", "****************")
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de "{data_documento}" Ass: "{nome_sindico}." - Síndico;"""
        else:
            cert_text += f"""

**{cert_counter}º) DECLARAÇÃO - NADA CONSTA DE DÉBITOS** - Que o imóvel nada deve em relação ao CONDOMÍNIO de que faz parte, até a presente data de *****************. Ass: **************** - Síndico;"""

    return cert_text


def format_rural_certificates_section(session: Dict[str, Any]) -> str:
    """Format rural certificates section"""
    certificates = []
    cert_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
    cert_index = 0

    certificates.append("3 - Foram-me apresentadas e ficam arquivadas as seguintes CERTIDÕES E DOCUMENTOS:")

    # A) Certidão de Ônus
    onus = session.get('certidoes', {}).get('onus', {})
    office_number = onus.get('Número do Ofício (apenas o número, ex: 1, 2, 3)', '1')
    city = onus.get('Cidade do Cartório', 'CIDADE')
    onus_date = onus.get('Data de expedição (dd/mm/aaaa)', '01/01/2024')

    cert_letter = cert_letters[cert_index]
    cert_index += 1
    certificates.append(f"{cert_letter}) A Certidão Negativa de Citações de Ações Reais e Pessoais Reipersecutórias e Ônus Reais, fornecida pelo Cartório do {office_number}º Ofício da Comarca de {city}-ES, datada de {onus_date}, onde o mesmo se acha livre de ônus;")

    # B-D) Indisponibilidade
    all_parties = session.get("vendedores", []) + session.get("compradores", [])
    for party in all_parties:
        if party.get("tipo") == "Pessoa Física":
            party_name = party.get("nome_completo", "NOME")
            party_cpf = party.get("cpf", "000.000.000-00")
            hash_code = generate_hash_code()

            cert_letter = cert_letters[cert_index]
            cert_index += 1
            certificates.append(f'{cert_letter}) Consulta a base de dados da Central Nacional de Indisponibilidade de Bens - CNIB, aos [DATE] às [TIME], em nome de {party_name}, CPF n° {party_cpf}, tendo a informação de "nenhum resultado encontrado para o filtro selecionado" e o código de HASH {hash_code};')

    # Process per-vendor certificates
    vendedores = session.get("vendedores", [])
    for vendor_idx, vendedor in enumerate(vendedores):
        if vendedor.get("tipo") == "Pessoa Física":
            vendor_name = vendedor.get("nome_completo", "VENDEDOR")
            vendor_cpf = vendedor.get("cpf", "000.000.000-00")

            shared_certs = ["negativa_federal", "debitos_tributarios", "negativa_estadual", "debitos_trabalhistas"]

            for cert_type in shared_certs:
                cert_data = session.get('certidoes', {}).get(f'{cert_type}_{vendor_idx}', {})

                if cert_data.get('dispensa'):
                    cert_letter = cert_letters[cert_index]
                    cert_index += 1
                    if cert_type == "negativa_federal":
                        certificates.append(f"{cert_letter}) Não pôde ser emitida a Certidão Conjunta Negativa de Débitos Relativos aos Tributos Federais e à Dívida Ativa da União, em nome de {vendor_name}, pela Internet por meio do endereço www.receita.fazenda.gov.br, aos [DATE], dispensando os Outorgados Compradores a apresentação da mesma;")
                else:
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

    # Property-level certificates
    itr = session.get('certidoes', {}).get('itr', {})
    if itr:
        cib_number = itr.get('Numero do CIB', 'CIB_NUMBER')
        control_code = itr.get('Codigo de controle', 'CTRL_CODE')
        issue_date = itr.get('Data de expedição (dd/mm/aaaa)', '01/01/2024')
        valid_until = itr.get('Data de Validade(dd/mm/aaaa)', '31/12/2024')

        cert_letter = cert_letters[cert_index]
        cert_index += 1
        certificates.append(f"{cert_letter}) A Certidão Negativa de Débitos Relativos ao Imposto sobre a Propriedade Territorial Rural, emitida pela Secretaria da Receita Federal do Brasil, sob o CIB nº. {cib_number}; código de controle {control_code}, aos {issue_date}, com validade até {valid_until}, pela Internet por meio do endereço www.receita.fazenda.gov.br;")

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
