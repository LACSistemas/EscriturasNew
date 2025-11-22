#!/usr/bin/env python
"""
Script para criar primeiro usuário administrador (VERSÃO AUTOMÁTICA PARA TESTES)
Uso: python scripts/create_admin_auto.py <email> <password>

Este script cria um usuário admin com is_superuser=True e is_approved=True
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import SessionLocal, create_db_and_tables
from models.user import User
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

# Password context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin(email: str, password: str):
    """Criar usuário administrador"""
    print("=" * 60)
    print("🔐 CRIAR ADMIN - Sistema de Escrituras (AUTO)")
    print("=" * 60)
    print()

    # Criar tabelas se não existirem
    print("📊 Criando tabelas do banco de dados...")
    try:
        create_db_and_tables()
        print("✅ Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

    print()
    print(f"📧 Email do admin: {email}")
    print(f"🔑 Senha: {'*' * len(password)}")
    print()
    print("⚙️  Criando usuário admin...")

    # Criar sessão do banco
    db = SessionLocal()

    try:
        # Verificar se já existe
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ Usuário {email} já existe!")
            print()
            print(f"Detalhes do usuário existente:")
            print(f"  - ID: {existing.id}")
            print(f"  - Email: {existing.email}")
            print(f"  - Ativo: {existing.is_active}")
            print(f"  - Aprovado: {existing.is_approved}")
            print(f"  - Superuser: {existing.is_superuser}")
            print(f"  - Criado em: {existing.created_at}")
            return False

        # Criar admin
        admin = User(
            email=email,
            hashed_password=pwd_context.hash(password),
            is_active=True,
            is_approved=True,  # Admin já aprovado automaticamente
            is_superuser=True,  # É superuser (admin)
            is_verified=True  # Email já verificado
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("=" * 60)
        print("✅ ADMIN CRIADO COM SUCESSO!")
        print("=" * 60)
        print()
        print(f"📧 Email: {admin.email}")
        print(f"🆔 ID: {admin.id}")
        print(f"✅ Ativo: {admin.is_active}")
        print(f"✅ Aprovado: {admin.is_approved}")
        print(f"👑 Superuser: {admin.is_superuser}")
        print(f"📅 Criado em: {admin.created_at}")
        print()
        print("🚀 Você pode fazer login agora usando:")
        print(f"   Email: {email}")
        print(f"   Senha: (a senha fornecida)")
        print()
        return True

    except IntegrityError as e:
        db.rollback()
        print(f"❌ Erro de integridade: {e}")
        print("   (Email provavelmente já existe)")
        return False
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar admin: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("❌ Uso: python scripts/create_admin_auto.py <email> <password>")
        print("   Exemplo: python scripts/create_admin_auto.py admin@example.com MySecurePass123")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    # Validações básicas
    if "@" not in email:
        print("❌ Email inválido (deve conter @)")
        sys.exit(1)

    if len(password) < 8:
        print("❌ Senha deve ter pelo menos 8 caracteres")
        sys.exit(1)

    success = create_admin(email, password)
    sys.exit(0 if success else 1)
