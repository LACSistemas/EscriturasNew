#!/usr/bin/env python
"""
Script para criar primeiro usuário administrador
Uso: python scripts/create_admin.py

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


def create_admin():
    """Criar usuário administrador"""
    print("=" * 60)
    print("🔐 CRIAR ADMIN - Sistema de Escrituras")
    print("=" * 60)
    print()

    # Criar tabelas se não existirem
    print("📊 Criando tabelas do banco de dados...")
    try:
        create_db_and_tables()
        print("✅ Tabelas criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return

    print()

    # Obter dados do admin
    email = input("📧 Email do admin: ").strip()
    if not email:
        print("❌ Email não pode estar vazio!")
        return

    password = input("🔑 Senha do admin (mínimo 8 caracteres): ").strip()
    if len(password) < 8:
        print("❌ Senha deve ter pelo menos 8 caracteres!")
        return

    password_confirm = input("🔑 Confirme a senha: ").strip()
    if password != password_confirm:
        print("❌ As senhas não coincidem!")
        return

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
            return

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
        print(f"   Senha: (a que você digitou)")
        print()
        print("📚 Endpoints disponíveis:")
        print("   - POST /auth/jwt/login - Fazer login")
        print("   - GET /users/me - Ver dados do usuário atual")
        print("   - GET /admin/users - Listar todos os usuários (admin only)")
        print()

    except IntegrityError as e:
        db.rollback()
        print(f"❌ Erro de integridade: {e}")
        print("   (Email provavelmente já existe)")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
