"""
Script para criar usuário administrador
"""
import asyncio
from sqlalchemy import select
from database import async_engine, AsyncSession
from models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    async with AsyncSession(async_engine) as session:
        # Verificar se já existe admin
        result = await session.execute(
            select(User).where(User.is_superuser == True)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"❌ Já existe um admin: {existing_admin.email}")
            return
        
        # Criar novo admin
        email = input("📧 Email do admin: ")
        password = input("🔒 Senha do admin: ")
        
        admin = User(
            email=email,
            hashed_password=pwd_context.hash(password),
            is_active=True,
            is_superuser=True,
            is_verified=True,
            is_approved=True
        )
        
        session.add(admin)
        await session.commit()
        
        print(f"✅ Admin criado com sucesso!")
        print(f"   Email: {email}")
        print(f"   Acesse: http://localhost:8000/admin/login")

if __name__ == "__main__":
    asyncio.run(create_admin())
