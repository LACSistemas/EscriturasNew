"""
Script para popular o banco de dados com templates padrão
Carrega os templates extraídos e os insere no banco para um usuário específico
"""
import json
from database import get_sync_db
from models.escritura_template import EscrituraTemplate
from models.user import User


def load_extracted_templates():
    """Carrega templates do arquivo JSON extraído"""
    with open('templates_padrao_extracted.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def populate_templates_for_user(user_id: int, db_session):
    """Popular templates padrão para um usuário específico"""

    print(f"\n🔄 Populando templates padrão para user_id={user_id}...")

    # Carregar templates extraídos
    templates_data = load_extracted_templates()

    created_count = 0
    skipped_count = 0

    for tipo_escritura, template_data in templates_data.items():
        # Verificar se usuário já tem template padrão deste tipo
        existing = db_session.query(EscrituraTemplate).filter(
            EscrituraTemplate.user_id == user_id,
            EscrituraTemplate.tipo_escritura == tipo_escritura,
            EscrituraTemplate.is_default == True,
            EscrituraTemplate.is_active == True
        ).first()

        if existing:
            print(f"  ⏭️  Tipo '{tipo_escritura}' já possui template padrão (ID: {existing.id}), pulando...")
            skipped_count += 1
            continue

        # Criar novo template
        new_template = EscrituraTemplate(
            user_id=user_id,
            tipo_escritura=template_data['tipo_escritura'],
            nome_template=template_data['nome_template'],
            template_json=template_data['template_json'],
            configuracoes_json=template_data['configuracoes_json'],
            is_default=True,
            is_active=True
        )

        db_session.add(new_template)
        print(f"  ✅ Criado template '{tipo_escritura}': {template_data['nome_template']}")
        created_count += 1

    # Commit todas as mudanças
    db_session.commit()

    print(f"\n📊 Resultado:")
    print(f"  ✅ Criados: {created_count}")
    print(f"  ⏭️  Pulados: {skipped_count}")

    return created_count


def populate_templates_all_users(db_session):
    """Popular templates padrão para TODOS os usuários que não têm"""

    print("\n🔄 Populando templates padrão para todos os usuários...")

    # Buscar todos os usuários
    users = db_session.query(User).filter(User.is_active == True).all()

    if not users:
        print("  ⚠️  Nenhum usuário encontrado no banco de dados!")
        return 0

    print(f"  Encontrados {len(users)} usuários ativos")

    total_created = 0

    for user in users:
        print(f"\n👤 Usuário: {user.email} (ID: {user.id})")
        created = populate_templates_for_user(user.id, db_session)
        total_created += created

    print(f"\n🎉 Total de templates criados: {total_created}")

    return total_created


def list_user_templates(user_id: int, db_session):
    """Lista todos os templates de um usuário"""

    templates = db_session.query(EscrituraTemplate).filter(
        EscrituraTemplate.user_id == user_id,
        EscrituraTemplate.is_active == True
    ).order_by(EscrituraTemplate.tipo_escritura).all()

    if not templates:
        print(f"  ℹ️  Usuário {user_id} não possui templates")
        return

    print(f"\n📋 Templates do usuário {user_id}:")
    for template in templates:
        default_mark = "⭐" if template.is_default else "  "
        blocos_count = len(template.template_json.get('blocos', []))
        print(f"  {default_mark} [{template.tipo_escritura:20s}] {template.nome_template:40s} ({blocos_count} blocos)")


def main():
    """Função principal"""
    import sys

    db = next(get_sync_db())

    try:
        if len(sys.argv) > 1:
            # Modo: popular para usuário específico
            user_id = int(sys.argv[1])

            # Verificar se usuário existe
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"❌ Usuário com ID {user_id} não encontrado!")
                return

            print(f"👤 Populando templates para: {user.email} (ID: {user.id})")
            populate_templates_for_user(user_id, db)

            # Listar templates do usuário
            list_user_templates(user_id, db)

        else:
            # Modo: popular para todos os usuários
            print("🌍 Modo: Popular templates para TODOS os usuários")
            print("    (Use 'python populate_default_templates.py <user_id>' para usuário específico)")

            populate_templates_all_users(db)

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
