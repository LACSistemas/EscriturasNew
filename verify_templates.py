"""
Script para verificar templates criados no banco
"""
from database import get_sync_db
from models.escritura_template import EscrituraTemplate
import json


def verify_template(template_id: int):
    """Verifica um template específico"""

    db = next(get_sync_db())

    try:
        template = db.query(EscrituraTemplate).filter(
            EscrituraTemplate.id == template_id
        ).first()

        if not template:
            print(f"❌ Template {template_id} não encontrado!")
            return

        print("="*70)
        print(f"📄 TEMPLATE ID: {template.id}")
        print("="*70)
        print(f"Tipo: {template.tipo_escritura}")
        print(f"Nome: {template.nome_template}")
        print(f"User ID: {template.user_id}")
        print(f"É padrão: {'Sim ⭐' if template.is_default else 'Não'}")
        print(f"Ativo: {'Sim' if template.is_active else 'Não'}")
        print(f"Criado em: {template.created_at}")
        print()

        # Estrutura do template_json
        template_json = template.template_json
        blocos = template_json.get('blocos', [])
        variaveis = template_json.get('variaveis_usadas', [])

        print(f"📦 BLOCOS ({len(blocos)}):")
        print("-"*70)
        for bloco in blocos:
            ordem = bloco.get('ordem', '?')
            tipo = bloco.get('tipo', 'sem tipo')
            conteudo_preview = bloco.get('conteudo', '')[:80].replace('\n', ' ')
            print(f"  {ordem}. [{tipo:25s}] {conteudo_preview}...")

        print()
        print(f"🔤 VARIÁVEIS ({len(variaveis)}):")
        print("-"*70)
        # Exibir variáveis em colunas
        for i in range(0, len(variaveis), 3):
            vars_slice = variaveis[i:i+3]
            vars_line = "  ".join(f"[{v}]" for v in vars_slice)
            print(f"  {vars_line}")

        # Configurações
        if template.configuracoes_json:
            print()
            print("⚙️  CONFIGURAÇÕES:")
            print("-"*70)
            config = template.configuracoes_json

            if 'terminologia' in config:
                print("  Terminologia:")
                for key, value in config['terminologia'].items():
                    print(f"    - {key}: {value}")

            if 'formatacao' in config:
                print("  Formatação:")
                for key, value in config['formatacao'].items():
                    print(f"    - {key}: {value}")

            if 'layout' in config:
                print("  Layout:")
                print(f"    - Fonte: {config['layout'].get('fonte', 'N/A')}")
                print(f"    - Tamanho: {config['layout'].get('tamanho_fonte_padrao', 'N/A')}")
                print(f"    - Espaçamento: {config['layout'].get('espacamento_entre_linhas', 'N/A')}")

        print("="*70)

    finally:
        db.close()


def list_all_templates():
    """Lista todos os templates do banco"""

    db = next(get_sync_db())

    try:
        templates = db.query(EscrituraTemplate).filter(
            EscrituraTemplate.is_active == True
        ).order_by(
            EscrituraTemplate.user_id,
            EscrituraTemplate.tipo_escritura
        ).all()

        print("\n📚 TODOS OS TEMPLATES NO BANCO:")
        print("="*70)

        current_user = None
        for template in templates:
            if current_user != template.user_id:
                current_user = template.user_id
                print(f"\n👤 User ID: {current_user}")
                print("-"*70)

            default_mark = "⭐" if template.is_default else "  "
            blocos_count = len(template.template_json.get('blocos', []))
            print(f"  {default_mark} ID {template.id:3d} | {template.tipo_escritura:20s} | {template.nome_template:40s} | {blocos_count:2d} blocos")

        print("="*70)
        print(f"Total: {len(templates)} templates")

    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Verificar template específico
        template_id = int(sys.argv[1])
        verify_template(template_id)
    else:
        # Listar todos
        list_all_templates()
