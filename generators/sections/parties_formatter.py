"""Party formatting for escrituras"""
from typing import List, Dict, Any
from utils.gender_utils import get_gender_agreement
from utils.date_formatter import format_birth_date, format_marriage_date
from utils.helpers import generate_hash_code


def format_parties(parties: List[Dict]) -> str:
    """Format party information for urban deeds"""
    formatted = []
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            # Get gender agreements for this person
            gender_agreement = get_gender_agreement(party)

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


def format_rural_parties(parties: List[Dict], is_vendedor: bool) -> str:
    """Format party information for rural escrituras"""
    if not parties:
        return "***PARTIES NOT FOUND***"

    formatted_parties = []

    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            gender_agreement = get_gender_agreement(party)
            gender = party.get("sexo", "").lower()
            honorific = "a Sra." if gender in ['feminino', 'f', 'female'] else "o Sr."

            nome_completo = party.get("nome_completo", "NOME_COMPLETO").upper()
            data_nascimento = format_birth_date(party.get("data_nascimento", "01/01/1980"))

            casado = party.get("casado", False)
            if casado:
                regime_bens = party.get("regime_bens", "Comunhão parcial de bens")
                marriage_info = f"casado sob o Regime da {regime_bens}"
                if party.get("data_casamento"):
                    marriage_date = format_marriage_date(party.get("data_casamento"))
                    marriage_info = f"casado aos {marriage_date}, sob o Regime da {regime_bens}"
                marital_status = marriage_info
            else:
                marital_status = "solteiro, não possui união estável"

            profissao = party.get("profissao", "produtor rural")

            documento_tipo = party.get("documento_tipo", "Carteira de Identidade")
            if documento_tipo == "Carteira de Identidade":
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da carteira de identidade e inscrito no CPF/MF sob o nº {cpf}"
            elif documento_tipo == "CNH":
                cnh_numero = party.get("cnh_numero", "00000000000")
                cnh_orgao = party.get("cnh_orgao_expedidor", "DETRAN/ES")
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da CNH nº {cnh_numero} expedida pelo {cnh_orgao} e inscrito no CPF/MF sob o nº {cpf}"
            else:
                ctps_numero = party.get("ctps_numero", "0000000")
                ctps_serie = party.get("ctps_serie", "0000")
                cpf = party.get("cpf", "000.000.000-00")
                doc_text = f"portador da CTPS nº {ctps_numero} série {ctps_serie}-ES e inscrito no CPF/MF sob o nº {cpf}"

            naturalidade = party.get("naturalidade", "Cariacica")
            pai_nome = party.get("pai_nome", "PAI_NOME_COMPLETO")
            mae_nome = party.get("mae_nome", "MAE_NOME_COMPLETO")
            endereco = party.get("endereco", "Endereço completo, Cidade-ES")

            party_prefix = "de um lado, como Outorgante Vendedor:" if is_vendedor else "e de outro lado na qualidade de Outorgado Comprador:"

            party_text = f"{party_prefix} {honorific} {nome_completo}, {gender_agreement['nascido']} aos {data_nascimento}, brasileiro, {marital_status}, {profissao}, {doc_text}, natural de {naturalidade}-ES, filho de {pai_nome} e de {mae_nome}, residente e domiciliado {endereco}"

            if casado and party.get("conjuge_assina") and party.get("conjuge_data"):
                conj = party["conjuge_data"]
                conj_gender_agreement = get_gender_agreement(conj)
                conj_gender = conj.get("sexo", "").lower()
                conj_honorific = "sua esposa" if conj_gender in ['feminino', 'f', 'female'] else "seu esposo"
                conj_sra_sr = "a Sra." if conj_gender in ['feminino', 'f', 'female'] else "o Sr."
                conj_nome = conj.get("nome_completo", "CONJUGE_NOME").upper()
                conj_nascimento = format_birth_date(conj.get("data_nascimento", "01/01/1980"))
                conj_profissao = conj.get("profissao", "lavradora" if conj_gender in ['feminino', 'f', 'female'] else "produtor rural")

                conj_doc_tipo = conj.get("documento_tipo", "Carteira de Identidade")
                if conj_doc_tipo == "Carteira de Identidade":
                    conj_cpf = conj.get("cpf", "000.000.000-00")
                    portador_word = "portadora" if conj_gender in ['feminino', 'f', 'female'] else "portador"
                    inscrito_word = "inscrita" if conj_gender in ['feminino', 'f', 'female'] else "inscrito"
                    conj_doc_text = f"{portador_word} da carteira de identidade e {inscrito_word} no CPF/MF sob o nº {conj_cpf}"
                elif conj_doc_tipo == "CNH":
                    conj_cnh_numero = conj.get("cnh_numero", "00000000000")
                    conj_cnh_orgao = conj.get("cnh_orgao_expedidor", "DETRAN/ES")
                    conj_cpf = conj.get("cpf", "000.000.000-00")
                    portador_word = "portadora" if conj_gender in ['feminino', 'f', 'female'] else "portador"
                    inscrito_word = "inscrita" if conj_gender in ['feminino', 'f', 'female'] else "inscrito"
                    conj_doc_text = f"{portador_word} da CNH nº {conj_cnh_numero} expedida pelo {conj_cnh_orgao} e {inscrito_word} no CPF/MF sob o nº {conj_cpf}"
                else:
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

        else:
            razao_social = party.get("razao_social", "EMPRESA NOME").upper()
            cnpj = party.get("cnpj", "00.000.000/0000-00")
            endereco_empresa = party.get("endereco", "Endereço da empresa, Cidade-ES")

            representative_name = "REPRESENTANTE NOME"
            representative_cpf = "000.000.000-00"
            representative_address = endereco_empresa

            party_prefix = "de um lado, como Outorgante Vendedor:" if is_vendedor else "e de outro lado na qualidade de Outorgado Comprador:"

            party_text = f"{party_prefix} {razao_social}, pessoa jurídica de direito privado, inscrita no CNPJ/MF sob o nº {cnpj}, com sede em {endereco_empresa}, neste ato representada por {representative_name}, brasileiro, casado, empresário, inscrito no CPF/MF sob o nº {representative_cpf}, residente e domiciliado {representative_address}"

            formatted_parties.append(party_text)

    return ";\n\n".join(formatted_parties)


def extract_party_names(parties: List[Dict], party_type: str) -> str:
    """Extract names for header with 'E' conjunction for multiple parties"""
    if not parties:
        return "***NAMES NOT FOUND***"

    names = []
    for party in parties:
        if party.get("tipo") == "Pessoa Física":
            nome = party.get("nome_completo", "NOME_COMPLETO").upper()
            names.append(nome)
        else:
            razao_social = party.get("razao_social", "EMPRESA_NOME").upper()
            names.append(razao_social)

    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} E {names[1]}"
    else:
        return ", ".join(names[:-1]) + f" E {names[-1]}"
