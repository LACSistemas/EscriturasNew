"""
Script para extrair templates dos generators existentes
Converte os generators Python em templates JSON para o Editor de Templates
"""
import json
import re
from typing import Dict, List, Any


def extract_lote_template() -> Dict[str, Any]:
    """Extrai template padrão para Lote"""

    template_json = {
        "blocos": [
            {
                "id": "bloco_1",
                "tipo": "cabecalho",
                "ordem": 1,
                "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA DE IMÓVEL URBANO\n\nSAIBAM quantos esta pública escritura de COMPRA E VENDA bastante virem que aos [DATA], às [HORA] horas, em meu Cartório, sito à [ENDERECO_CARTORIO], perante mim [QUEM_ASSINA],",
                "formatacao": {
                    "negrito": True,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "center"
                }
            },
            {
                "id": "bloco_2",
                "tipo": "identificacao_partes",
                "ordem": 2,
                "conteudo": "compareceram partes entre si, justas e convencionadas: de um lado como [VENDEDOR_TITULO]: [VENDEDOR_DADOS_COMPLETOS]; e de outro lado, como [COMPRADOR_TITULO]: [COMPRADOR_DADOS_COMPLETOS];",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_3",
                "tipo": "autenticacao",
                "ordem": 3,
                "conteudo": "Sendo as presentes pessoas reconhecidas como as próprias de que trato por mim [QUEM_ASSINA], de cuja identidade e capacidade jurídica, DOU FÉ.",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_4",
                "tipo": "descricao_imovel",
                "ordem": 4,
                "conteudo": "E pelo [VENDEDOR_TITULO] referido, foi dito que é dono, senhor e legítimo possuidor, absolutamente livre e desembaraçado de todo e qualquer ônus real, do imóvel constituído pelo: [IMOVEL_DESCRICAO]; devidamente registrado no Cartório de Registro Geral de Imóveis do [OFICIO_NUMERO]º Ofício - [ZONA_CARTORIO] - [CIDADE_CARTORIO], matrícula nº [MATRICULA_NUMERO] do livro nº [LIVRO_NUMERO], com valor venal atribuído pela municipalidade local de [VALOR_VENAL];",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_5",
                "tipo": "clausula_venda",
                "ordem": 5,
                "conteudo": "que assim possuindo o referido imóvel, vende ao [COMPRADOR_TITULO], como efetivamente vendido tem, por bem desta escritura, da cláusula CONSTITUTI, e na melhor forma de direito, pelo preço certo e ajustado de [VALOR_IMOVEL], pago [FORMA_PAGAMENTO] em moeda corrente nacional através de [MEIO_PAGAMENTO], do que desde já, lhes dá plena, rasa e geral quitação da importância recebida, para nada mais exigirem com relação a presente venda, transmitindo, como de fato ora transmite na pessoa do [COMPRADOR_TITULO], todo direito, posse, domínio e ação que exerciam sobre o referido imóvel, e prometendo por si e seus sucessores legítimos a presente venda, boa, firme e valiosa para sempre, obrigando-se a responderem pela evicção de direito, se chamado a autoria.",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_6",
                "tipo": "aceitacao_comprador",
                "ordem": 6,
                "conteudo": "Pelo [COMPRADOR_TITULO], me foi dito que, aceita a presente escritura como nela se contém e declara, por estar o mesmo de inteiro acordo com o ajustado e contratado entre si e o [VENDEDOR_TITULO].",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_7",
                "tipo": "certidoes",
                "ordem": 7,
                "conteudo": "Foram apresentadas as seguintes certidões:\n\n[LISTA_CERTIDOES]",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_8",
                "tipo": "declaracoes",
                "ordem": 8,
                "conteudo": """**Declarações:**

**Do [COMPRADOR_TITULO]:**

a.1) Concorda com os termos desta escritura;

a.2) Declara que tem conhecimento de que o valor declarado do imóvel é o valor de referência que foi declarado pelo vendedor e que, está sujeito à avaliação, pela municipalidade, de forma que, em caso de avaliação em valor superior ao mencionado nesta escritura, haverá diferença de emolumentos a pagar junto ao Tabelionato de Notas, conforme determinado no artigo 59, parágrafo único da Lei Estadual nº 3.151/78.

a.3) Que está ciente, assim, nos termos do item anterior, que caso o imóvel seja avaliado pela municipalidade em valor superior ao declarado, será necessário promover o aditamento da presente Escritura e realizar a devida complementação de emolumentos.

**Do [VENDEDOR_TITULO]:**

b.1) Sob responsabilidade civil e penal, que sobre o imóvel objeto da presente escritura não incide nenhuma ação ou pendência judicial ou extrajudicial, nem ações reais e pessoais reipersecutórias e nem outros ônus reais;

b.2) Não existir débitos condominiais, ordinários e extraordinários, referente aos imóveis objetos da presente escritura pública. De acordo com o artigo 649, parágrafo único do Código de Normas da Egrégia Corregedoria Geral de Justiça do Estado do Espírito Santo, as partes foram orientadas "que a ausência da referida prova não isenta os responsáveis, de acordo com a lei civil, ao pagamento do débito condominial, dando ciência e fazendo constar expressamente da escritura que o adquirente, mesmo ciente de que passa a responder pelos débitos do alienante, em relação ao condomínio, inclusive multa e juros (CC art. 1.345), dispensou a apresentação da prova de quitação das obrigações de que trata o caput deste artigo", qual seja, os débitos condominiais;""",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_9",
                "tipo": "clausulas_finais",
                "ordem": 9,
                "conteudo": """**Declarações Gerais:**

c.1) Declaram as partes que estão cientes que este ato importa em comunicação obrigatória prevista na Instrução Normativa nº 1.571, de 02 de julho de 2015, para fins de intercâmbio de informações entre os tabeliães de notas, os oficiais de registro de imóveis e a Secretaria da Receita Federal do Brasil - RFB, por isso, a DOI (Declaração de Operação Imobiliária), relativa ao presente instrumento, será emitida regularmente e enviada à Receita Federal, até o último dia útil do mês subseqüente ao da lavratura desta escritura;

c.2) Concordam com todos os termos e condições acima mencionados, e a pedido delas, lavro a escritura em meu livro de notas;

c.3) Que para fins de cumprimento do provimento do CNJ nº 88/2019, não são pessoas politicamente expostas e, nem são parentes de até 1º grau de pessoas politicamente expostas, bem como, não são estreitos colaboradores de pessoas politicamente expostas;

c.4) As partes requerem ao Oficial de Registro de Imóveis competente, que promova na matrícula antes mencionada, todos e quaisquer atos de registros e de averbações que se fizerem necessárias para o fiel cumprimento do registro desta escritura, junto ao Registro de Imóveis competente.

c.5) As partes envolvidas neste ato foram cientificadas da possibilidade de obtenção da Certidão Negativa de Débitos Trabalhistas (CNDT), nos termos do artigo 642-A do CLT; A DOI referente ao presente instrumento será emitida regularmente e enviada à SRF, no prazo estabelecido pela IN n.° 1.112 RFB de 28/12/2010.

c.6) Todas as partes foram informadas por esta serventia da proibição e ilegalidade de concessão de descontos ou comissões na cobrança dos emolumentos, nos termos dos artigos 6º, inciso XVIII e 7º, incisos III e IV do Provimento da CGJ/ES nº 07/2024 (Código de ética e de conduta dos responsáveis pelas serventias extrajudiciais do Estado do Espírito Santo), sem prejuízo da apuração de condutas que constituam falta disciplinar, nos termos da lei e dos regulamentos da Corregedoria Geral da Justiça, ficando ressalvadas as hipóteses legais".""",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            }
        ],
        "variaveis_usadas": [
            "DATA", "HORA", "ENDERECO_CARTORIO", "QUEM_ASSINA",
            "VENDEDOR_TITULO", "VENDEDOR_DADOS_COMPLETOS",
            "COMPRADOR_TITULO", "COMPRADOR_DADOS_COMPLETOS",
            "IMOVEL_DESCRICAO", "OFICIO_NUMERO", "ZONA_CARTORIO",
            "CIDADE_CARTORIO", "MATRICULA_NUMERO", "LIVRO_NUMERO",
            "VALOR_VENAL", "VALOR_IMOVEL", "FORMA_PAGAMENTO",
            "MEIO_PAGAMENTO", "LISTA_CERTIDOES"
        ]
    }

    configuracoes_json = {
        "terminologia": {
            "vendedor": "VENDEDOR",
            "comprador": "COMPRADOR",
            "imovel": "IMÓVEL"
        },
        "formatacao": {
            "titulos_negrito": True,
            "variaveis_destacadas": True,
            "numeracao_automatica": True
        },
        "layout": {
            "margem_superior": 2.5,
            "margem_inferior": 2.5,
            "margem_esquerda": 3.0,
            "margem_direita": 3.0,
            "espacamento_entre_linhas": 1.5,
            "fonte": "Times New Roman",
            "tamanho_fonte_padrao": 12
        }
    }

    return {
        "tipo_escritura": "lote",
        "nome_template": "Template Padrão - Lote Urbano",
        "template_json": template_json,
        "configuracoes_json": configuracoes_json,
        "is_default": True
    }


def extract_apto_template() -> Dict[str, Any]:
    """Extrai template padrão para Apartamento (similar ao lote, com pequenas diferenças)"""

    lote_template = extract_lote_template()
    apto_template = json.loads(json.dumps(lote_template))  # Deep copy

    # Modificar para apartamento
    apto_template["tipo_escritura"] = "apto"
    apto_template["nome_template"] = "Template Padrão - Apartamento"

    # Alterar cabeçalho
    apto_template["template_json"]["blocos"][0]["conteudo"] = "ESCRITURA PÚBLICA DE COMPRA E VENDA DE APARTAMENTO\n\nSAIBAM quantos esta pública escritura de COMPRA E VENDA bastante virem que aos [DATA], às [HORA] horas, em meu Cartório, sito à [ENDERECO_CARTORIO], perante mim [QUEM_ASSINA],"

    # Adicionar bloco específico de condomínio
    condominio_bloco = {
        "id": "bloco_condominio",
        "tipo": "condominio",
        "ordem": 5,
        "conteudo": "Apartamento situado em condomínio edilício, sujeito às normas da convenção condominial e regimento interno, conforme [CERTIDAO_CONDOMINIO].",
        "formatacao": {
            "negrito": False,
            "italico": False,
            "sublinhado": False,
            "alinhamento": "justify"
        }
    }

    # Inserir bloco de condomínio após descrição do imóvel
    apto_template["template_json"]["blocos"].insert(4, condominio_bloco)

    # Reordenar
    for i, bloco in enumerate(apto_template["template_json"]["blocos"], start=1):
        bloco["ordem"] = i

    # Adicionar variável de condomínio
    apto_template["template_json"]["variaveis_usadas"].append("CERTIDAO_CONDOMINIO")

    return apto_template


def extract_rural_template() -> Dict[str, Any]:
    """Extrai template padrão para Rural"""

    template_json = {
        "blocos": [
            {
                "id": "bloco_1",
                "tipo": "cabecalho",
                "ordem": 1,
                "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA DE IMÓVEL RURAL",
                "formatacao": {
                    "negrito": True,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "center"
                }
            },
            {
                "id": "bloco_2",
                "tipo": "saibam",
                "ordem": 2,
                "conteudo": "S A I B A M quantos esta pública escritura de COMPRA E VENDA bastante virem que aos [DATA], às 10:00 horas, em meu Cartório, sito à [ENDERECO_CARTORIO], perante mim [QUEM_ASSINA], compareceram partes entre sí, justas e convencionadas, a saber,",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_3",
                "tipo": "outorgante_vendedor",
                "ordem": 3,
                "conteudo": "como OUTORGANTE VENDEDOR: [VENDEDOR_DADOS_RURAIS_COMPLETOS]",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_4",
                "tipo": "outorgado_comprador",
                "ordem": 4,
                "conteudo": "e como OUTORGADO COMPRADOR: [COMPRADOR_DADOS_RURAIS_COMPLETOS]",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_5",
                "tipo": "autenticacao",
                "ordem": 5,
                "conteudo": "Sendo as presentes pessoas reconhecidas como as próprias de que trato por mim [QUEM_ASSINA], de cuja identidade e capacidade jurídica, DOU FÉ.",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_6",
                "tipo": "descricao_imovel_rural",
                "ordem": 6,
                "conteudo": """1 - DO OBJETO: 1.1 - Pelo Outorgante Vendedor, me foi dito que é legítimo dono, senhor e possuidor do imóvel constituído por: [IMOVEL_DESCRICAO_RURAL_COMPLETA]

Conforme certidão de matrícula nº [MATRICULA_NUMERO], registrado no livro nº [LIVRO_NUMERO], no Cartório de Registro de Imóveis de [CIDADE_CARTORIO].""",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_7",
                "tipo": "clausula_venda_rural",
                "ordem": 7,
                "conteudo": "1.2 - e achando-se contratado, com os Outorgados Compradores, por bem desta escritura, e na melhor forma de direito para lhe vender, como de fato vendido tem o imóvel descrito pelo preço certo e ajustado de direito por [VALOR_IMOVEL] ([VALOR_IMOVEL_EXTENSO]), pago em espécie na data de hoje, aqui; importância essa que o Outorgante Vendedor confessa e declara haver recebido em moeda corrente, pelo que se dá por pago e satisfeito, e por isso dá plena, geral e irrevogável quitação deste pagamento para nunca mais o repetirem, desde já transferindo-lhes toda a posse, domínio, direito e ação que exercia sobre o imóvel ora vendido, respondendo pela evicção de direito, quando chamados à autoria.",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_8",
                "tipo": "disposicoes_gerais_rural",
                "ordem": 8,
                "conteudo": """2. - DAS DISPOSIÇÕES GERAIS: 2.1 - Os comparecentes declaram que: a) sob responsabilidade civil e criminal que os fatos aqui relatados e declarações feitas são exata expressão da verdade; b) foram informados que qualquer pessoa pode ter acesso às informações aqui prestadas; c) estão cientes de que esta pública escritura deverá ser registrada no Registro de Imóveis competente; d) fazem a manifestação da vontade nesta escritura sempre boa, firme e valiosa, afirmando que são verdadeiras e isentas de vícios.

2.13- As partes declaram que têm conhecimento da necessidade de se apresentar o CAR (Cadastro Ambiental Rural) no ato do registro de imóveis.

2.14 - As partes declaram que têm conhecimento de que a partir de 20 de novembro de 2025, será necessário apresentar o georreferenciamento certificado pelo INCRA.""",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_9",
                "tipo": "certidoes_rurais",
                "ordem": 9,
                "conteudo": "3 - DAS CERTIDÕES APRESENTADAS:\n\n[LISTA_CERTIDOES_RURAIS]",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            },
            {
                "id": "bloco_10",
                "tipo": "notas_explicativas",
                "ordem": 10,
                "conteudo": """4 - DAS NOTAS EXPLICATIVAS: 4.1 - As partes estão cientes de que a cobrança dos emolumentos da presente Escritura Pública está de acordo com a Lei Estadual nº 3.151/78.

Foi emitida a Declaração sobre a Operação Imobiliária (DOI) conforme IN/RFB nº 1.112/10.

Declara o Outorgante Vendedor, que para fins de direito, não é contribuinte obrigatório do INSS.

Declaram os Outorgados Compradores, sob pena da Lei, que o imóvel da presente transação não será utilizado como depósito de agrotóxicos, radioativos ou que venha a produzir poluição ambiental de qualquer natureza.

ASSIM O DISSERAM do que dou fé e me pediram este instrumento que lhes li, aceitaram e assinam, [DATA]""",
                "formatacao": {
                    "negrito": False,
                    "italico": False,
                    "sublinhado": False,
                    "alinhamento": "justify"
                }
            }
        ],
        "variaveis_usadas": [
            "DATA", "ENDERECO_CARTORIO", "QUEM_ASSINA",
            "VENDEDOR_DADOS_RURAIS_COMPLETOS",
            "COMPRADOR_DADOS_RURAIS_COMPLETOS",
            "IMOVEL_DESCRICAO_RURAL_COMPLETA",
            "MATRICULA_NUMERO", "LIVRO_NUMERO", "CIDADE_CARTORIO",
            "VALOR_IMOVEL", "VALOR_IMOVEL_EXTENSO",
            "LISTA_CERTIDOES_RURAIS",
            "CERTIDAO_ITR", "CERTIDAO_CCIR", "CERTIDAO_INCRA", "CERTIDAO_IBAMA"
        ]
    }

    configuracoes_json = {
        "terminologia": {
            "vendedor": "OUTORGANTE VENDEDOR",
            "comprador": "OUTORGADO COMPRADOR",
            "imovel": "IMÓVEL RURAL"
        },
        "formatacao": {
            "titulos_negrito": True,
            "variaveis_destacadas": True,
            "numeracao_automatica": True
        },
        "layout": {
            "margem_superior": 2.5,
            "margem_inferior": 2.5,
            "margem_esquerda": 3.0,
            "margem_direita": 3.0,
            "espacamento_entre_linhas": 1.5,
            "fonte": "Times New Roman",
            "tamanho_fonte_padrao": 12
        }
    }

    return {
        "tipo_escritura": "rural",
        "nome_template": "Template Padrão - Imóvel Rural",
        "template_json": template_json,
        "configuracoes_json": configuracoes_json,
        "is_default": True
    }


def extract_rural_desmembramento_template() -> Dict[str, Any]:
    """Extrai template padrão para Rural com Desmembramento"""

    rural_template = extract_rural_template()
    desm_template = json.loads(json.dumps(rural_template))  # Deep copy

    # Modificar para desmembramento
    desm_template["tipo_escritura"] = "rural_desmembramento"
    desm_template["nome_template"] = "Template Padrão - Rural com Desmembramento"

    # Alterar cabeçalho
    desm_template["template_json"]["blocos"][0]["conteudo"] = "ESCRITURA PÚBLICA DE COMPRA E VENDA DE IMÓVEL RURAL COM DESMEMBRAMENTO"

    # Adicionar bloco de desmembramento após a descrição do imóvel
    desmembramento_bloco = {
        "id": "bloco_desmembramento",
        "tipo": "desmembramento",
        "ordem": 7,
        "conteudo": """DESMEMBRAMENTO: O imóvel acima descrito foi objeto de desmembramento, conforme:
- ART de Desmembramento: [CERTIDAO_ART_DESMEMBRAMENTO]
- Planta de Desmembramento: [CERTIDAO_PLANTA_DESMEMBRAMENTO]
- Aprovação: [APROVACAO_DESMEMBRAMENTO]

O lote vendido corresponde ao lote [NUMERO_LOTE_DESMEMBRADO] do desmembramento aprovado.""",
        "formatacao": {
            "negrito": False,
            "italico": False,
            "sublinhado": False,
            "alinhamento": "justify"
        }
    }

    # Inserir após descrição do imóvel (índice 6)
    desm_template["template_json"]["blocos"].insert(6, desmembramento_bloco)

    # Reordenar
    for i, bloco in enumerate(desm_template["template_json"]["blocos"], start=1):
        bloco["ordem"] = i

    # Adicionar variáveis de desmembramento
    desm_template["template_json"]["variaveis_usadas"].extend([
        "CERTIDAO_ART_DESMEMBRAMENTO",
        "CERTIDAO_PLANTA_DESMEMBRAMENTO",
        "APROVACAO_DESMEMBRAMENTO",
        "NUMERO_LOTE_DESMEMBRADO"
    ])

    return desm_template


def main():
    """Extrai todos os templates e salva em arquivo JSON"""

    print("🔄 Extraindo templates dos generators...")

    templates = {
        "lote": extract_lote_template(),
        "apto": extract_apto_template(),
        "rural": extract_rural_template(),
        "rural_desmembramento": extract_rural_desmembramento_template()
    }

    # Salvar em arquivo JSON
    output_file = "templates_padrao_extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

    print(f"✅ Templates extraídos e salvos em: {output_file}")

    # Exibir resumo
    print("\n📊 Resumo dos Templates Extraídos:")
    for tipo, template in templates.items():
        blocos_count = len(template['template_json']['blocos'])
        vars_count = len(template['template_json']['variaveis_usadas'])
        print(f"  - {tipo}: {blocos_count} blocos, {vars_count} variáveis")
        print(f"    Nome: {template['nome_template']}")

    return templates


if __name__ == "__main__":
    templates = main()
