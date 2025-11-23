"""
Teste direto do modelo EscrituraTemplate (sem API)
Testa criação, leitura e funções do modelo diretamente no banco
"""
from database import get_sync_db
from models.escritura_template import EscrituraTemplate
from models.user import User

def print_section(title):
    """Imprime seção formatada"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def main():
    """Teste direto do modelo"""
    print("🧪 TESTE DIRETO DO MODELO ESCRITURA_TEMPLATE")

    # Get database session
    db = next(get_sync_db())

    try:
        # 1. Buscar usuário de teste
        print_section("1. BUSCAR USUÁRIO DE TESTE")
        user = db.query(User).filter(User.email == "test@escrituras.com").first()
        if not user:
            print("❌ Usuário test@escrituras.com não encontrado")
            return
        print(f"✅ Usuário encontrado: {user.email} (ID: {user.id})")
        print(f"   Aprovado: {user.is_approved}")

        # 2. Criar template de teste
        print_section("2. CRIAR TEMPLATE DE TESTE")
        template_data = {
            "blocos": [
                {
                    "id": "bloco_1",
                    "tipo": "cabecalho",
                    "ordem": 1,
                    "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA",
                    "formatacao": {
                        "negrito": True,
                        "italico": False,
                        "sublinhado": False,
                        "alinhamento": "center"
                    }
                },
                {
                    "id": "bloco_2",
                    "tipo": "partes",
                    "ordem": 2,
                    "conteudo": "COMPRADOR: [COMPRADOR_NOME], CPF [COMPRADOR_CPF]",
                    "formatacao": {
                        "negrito": False,
                        "italico": False,
                        "sublinhado": False,
                        "alinhamento": "justify"
                    }
                },
                {
                    "id": "bloco_3",
                    "tipo": "partes",
                    "ordem": 3,
                    "conteudo": "VENDEDOR: [VENDEDOR_NOME], CPF [VENDEDOR_CPF]",
                    "formatacao": {
                        "negrito": False,
                        "italico": False,
                        "sublinhado": False,
                        "alinhamento": "justify"
                    }
                }
            ],
            "variaveis_usadas": [
                "COMPRADOR_NOME",
                "COMPRADOR_CPF",
                "VENDEDOR_NOME",
                "VENDEDOR_CPF"
            ]
        }

        config_data = {
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

        template = EscrituraTemplate(
            user_id=user.id,
            tipo_escritura="lote",
            nome_template="Template Teste Direto - Lote Urbano",
            template_json=template_data,
            configuracoes_json=config_data,
            is_default=True,
            is_active=True
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        print(f"✅ Template criado com sucesso!")
        print(f"   ID: {template.id}")
        print(f"   Nome: {template.nome_template}")
        print(f"   Tipo: {template.tipo_escritura}")
        print(f"   É padrão: {template.is_default}")
        print(f"   Total de blocos: {template.total_blocos}")
        print(f"   Variáveis: {', '.join(template.variaveis_usadas)}")

        template_id = template.id

        # 3. Listar templates do usuário
        print_section("3. LISTAR TEMPLATES DO USUÁRIO")
        templates = db.query(EscrituraTemplate).filter(
            EscrituraTemplate.user_id == user.id,
            EscrituraTemplate.is_active == True
        ).all()

        print(f"✅ Total de templates: {len(templates)}")
        for t in templates:
            print(f"   - ID {t.id}: {t.nome_template} ({t.tipo_escritura}) {'⭐' if t.is_default else ''}")

        # 4. Buscar template específico
        print_section(f"4. BUSCAR TEMPLATE {template_id}")
        found_template = db.query(EscrituraTemplate).filter(
            EscrituraTemplate.id == template_id
        ).first()

        if found_template:
            print(f"✅ Template encontrado!")
            print(f"   Nome: {found_template.nome_template}")
            print(f"   Blocos:")
            for bloco in found_template.template_json["blocos"]:
                print(f"      {bloco['ordem']}. [{bloco['tipo']}] {bloco['conteudo'][:50]}...")

        # 5. Buscar template padrão
        print_section("5. BUSCAR TEMPLATE PADRÃO PARA 'LOTE'")
        default_template = db.query(EscrituraTemplate).filter(
            EscrituraTemplate.user_id == user.id,
            EscrituraTemplate.tipo_escritura == "lote",
            EscrituraTemplate.is_default == True,
            EscrituraTemplate.is_active == True
        ).first()

        if default_template:
            print(f"✅ Template padrão encontrado!")
            print(f"   ID: {default_template.id}")
            print(f"   Nome: {default_template.nome_template}")

        # 6. Testar to_dict()
        print_section("6. TESTAR MÉTODO to_dict()")
        template_dict = found_template.to_dict()
        print(f"✅ Conversão para dict bem-sucedida!")
        print(f"   Chaves: {', '.join(template_dict.keys())}")

        print_section("TESTES CONCLUÍDOS ✅")
        print("Modelo EscrituraTemplate funcionando corretamente!")

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
