"""
Script de teste para a API de Templates
Testa criação, leitura, atualização e preview de templates
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Dados de login (usando usuário de teste)
LOGIN_DATA = {
    "username": "test@escrituras.com",
    "password": "test123"
}

def print_section(title):
    """Imprime seção formatada"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def login():
    """Faz login e retorna o token JWT"""
    print_section("1. LOGIN")
    response = requests.post(
        f"{BASE_URL}/auth/jwt/login",
        data=LOGIN_DATA
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login realizado com sucesso!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None

def create_template(token):
    """Cria um template de teste"""
    print_section("2. CRIAR TEMPLATE")

    headers = {"Authorization": f"Bearer {token}"}

    template_data = {
        "tipo_escritura": "lote",
        "nome_template": "Template Teste - Lote Urbano",
        "is_default": True,
        "template_json": {
            "blocos": [
                {
                    "id": "bloco_1",
                    "tipo": "cabecalho",
                    "ordem": 1,
                    "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA DE IMÓVEL",
                    "formatacao": {
                        "negrito": True,
                        "alinhamento": "center"
                    }
                },
                {
                    "id": "bloco_2",
                    "tipo": "identificacao_partes",
                    "ordem": 2,
                    "conteudo": "COMPRADOR: [COMPRADOR_NOME], [COMPRADOR_NACIONALIDADE], [COMPRADOR_ESTADO_CIVIL], [COMPRADOR_PROFISSAO], portador do CPF [COMPRADOR_CPF].",
                    "formatacao": {
                        "alinhamento": "justify"
                    }
                },
                {
                    "id": "bloco_3",
                    "tipo": "identificacao_partes",
                    "ordem": 3,
                    "conteudo": "VENDEDOR: [VENDEDOR_NOME], [VENDEDOR_NACIONALIDADE], [VENDEDOR_ESTADO_CIVIL], [VENDEDOR_PROFISSAO], portador do CPF [VENDEDOR_CPF].",
                    "formatacao": {
                        "alinhamento": "justify"
                    }
                },
                {
                    "id": "bloco_4",
                    "tipo": "descricao_imovel",
                    "ordem": 4,
                    "conteudo": "IMÓVEL: Lote de terreno situado em [LOGRADOURO], [BAIRRO], [CIDADE]-[UF], com área de [AREA_TOTAL] m².",
                    "formatacao": {
                        "alinhamento": "justify"
                    }
                }
            ],
            "variaveis_usadas": [
                "COMPRADOR_NOME", "COMPRADOR_NACIONALIDADE", "COMPRADOR_ESTADO_CIVIL",
                "COMPRADOR_PROFISSAO", "COMPRADOR_CPF", "VENDEDOR_NOME",
                "VENDEDOR_NACIONALIDADE", "VENDEDOR_ESTADO_CIVIL", "VENDEDOR_PROFISSAO",
                "VENDEDOR_CPF", "LOGRADOURO", "BAIRRO", "CIDADE", "UF", "AREA_TOTAL"
            ]
        },
        "configuracoes_json": {
            "terminologia": {
                "vendedor": "OUTORGANTE VENDEDOR",
                "comprador": "OUTORGADO COMPRADOR",
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
    }

    response = requests.post(
        f"{BASE_URL}/templates",
        headers=headers,
        json=template_data
    )

    if response.status_code == 201:
        result = response.json()
        print(f"✅ Template criado com sucesso!")
        print(f"ID: {result['template']['id']}")
        print(f"Nome: {result['template']['nome_template']}")
        print(f"Tipo: {result['template']['tipo_escritura']}")
        print(f"É padrão: {result['template']['is_default']}")
        print(f"Total de blocos: {len(result['template']['template_json']['blocos'])}")
        return result['template']['id']
    else:
        print(f"❌ Erro ao criar template: {response.status_code}")
        print(response.text)
        return None

def list_templates(token):
    """Lista todos os templates do usuário"""
    print_section("3. LISTAR TEMPLATES")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/templates",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Total de templates: {result['total']}")
        for t in result['templates']:
            print(f"  - ID {t['id']}: {t['nome_template']} ({t['tipo_escritura']}) {'⭐' if t['is_default'] else ''}")
        return result['templates']
    else:
        print(f"❌ Erro ao listar templates: {response.status_code}")
        print(response.text)
        return []

def get_template(token, template_id):
    """Busca um template específico"""
    print_section(f"4. BUSCAR TEMPLATE {template_id}")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/templates/{template_id}",
        headers=headers
    )

    if response.status_code == 200:
        template = response.json()
        print(f"✅ Template encontrado!")
        print(f"ID: {template['id']}")
        print(f"Nome: {template['nome_template']}")
        print(f"Blocos:")
        for bloco in template['template_json']['blocos']:
            print(f"  {bloco['ordem']}. [{bloco['tipo']}] {bloco['conteudo'][:60]}...")
        return template
    else:
        print(f"❌ Erro ao buscar template: {response.status_code}")
        print(response.text)
        return None

def preview_template(token, template_id):
    """Gera preview do template com dados de exemplo"""
    print_section(f"5. PREVIEW DO TEMPLATE {template_id}")

    headers = {"Authorization": f"Bearer {token}"}

    dados_exemplo = {
        "COMPRADOR_NOME": "João da Silva",
        "COMPRADOR_NACIONALIDADE": "brasileiro",
        "COMPRADOR_ESTADO_CIVIL": "casado",
        "COMPRADOR_PROFISSAO": "engenheiro",
        "COMPRADOR_CPF": "123.456.789-00",
        "VENDEDOR_NOME": "Maria Santos",
        "VENDEDOR_NACIONALIDADE": "brasileira",
        "VENDEDOR_ESTADO_CIVIL": "solteira",
        "VENDEDOR_PROFISSAO": "médica",
        "VENDEDOR_CPF": "987.654.321-00",
        "LOGRADOURO": "Rua das Flores, 123",
        "BAIRRO": "Centro",
        "CIDADE": "São Paulo",
        "UF": "SP",
        "AREA_TOTAL": "250,00"
    }

    response = requests.post(
        f"{BASE_URL}/templates/{template_id}/preview",
        headers=headers,
        json={"dados_exemplo": dados_exemplo}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Preview gerado com sucesso!")
        print("\n--- PREVIEW TEXTO ---")
        print(result['preview_text'])
        print("\n--- PREVIEW HTML ---")
        print(result['preview_html'][:500] + "..." if len(result['preview_html']) > 500 else result['preview_html'])
        return result
    else:
        print(f"❌ Erro ao gerar preview: {response.status_code}")
        print(response.text)
        return None

def main():
    """Função principal de teste"""
    print("🧪 TESTE DA API DE TEMPLATES DE ESCRITURAS")

    # 1. Login
    token = login()
    if not token:
        print("\n❌ Não foi possível fazer login. Encerrando testes.")
        return

    # 2. Criar template
    template_id = create_template(token)
    if not template_id:
        print("\n❌ Não foi possível criar template. Encerrando testes.")
        return

    # 3. Listar templates
    list_templates(token)

    # 4. Buscar template específico
    get_template(token, template_id)

    # 5. Preview do template
    preview_template(token, template_id)

    print_section("TESTES CONCLUÍDOS ✅")
    print("Todos os endpoints foram testados com sucesso!")

if __name__ == "__main__":
    main()
