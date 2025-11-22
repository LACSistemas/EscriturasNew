"""FastAPI application - Async & Modern Architecture"""
import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Import configuration and initialization
from config import config, MAX_CONTENT_LENGTH
from database import create_db_and_tables

# Import FastAPI routers
from routes.health_routes_fastapi import router as health_router
# from routes.auth_routes_fastapi import router as old_auth_router  # Old auth (deprecated - using FastAPI Users)
# from routes.cartorio_routes_fastapi import router as cartorio_router  # Disabled due to missing database functions
from routes.process_routes_sm import router as process_sm_router, set_clients as set_clients_sm
from routes.admin_routes import router as admin_router  # Admin panel
from routes.cartorio_config_routes import router as cartorio_config_router  # Cartorio configuration

# Import FastAPI Users auth system
from auth.users import fastapi_users, auth_backend
from models.user_schemas import UserRead, UserCreate, UserUpdate

# Import models (para criar tabelas)
from models.user import User
from models.cartorio_config import CartorioConfig

# Force unbuffered output
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Processor",
    description="Sistema de geração automática de escrituras usando OCR e IA",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (para Streamlit acessar a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default port
        "http://127.0.0.1:8501",
        "*"  # Allow all for development (configure appropriately for production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Note: Database tables will be created on startup event (see below)

# Initialize external clients
config.initialize_vision_client()
config.initialize_gemini_client()

# Set clients for State Machine routes
set_clients_sm(config.get_vision_client(), config.get_gemini_model())

# Register routers
app.include_router(health_router)
# app.include_router(old_auth_router)  # Old auth (deprecated - using FastAPI Users)
# app.include_router(cartorio_router)  # Disabled due to missing database functions
app.include_router(process_sm_router)  # State Machine endpoint

# FastAPI Users routers (New Auth System)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)

# Admin panel router
app.include_router(admin_router)

# Cartorio configuration router
app.include_router(cartorio_config_router)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    # Create database tables
    try:
        create_db_and_tables()
        logger.info("✅ Database tables created successfully!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    logger.info("🚀 FastAPI application started successfully!")
    logger.info("📚 API documentation available at /docs")
    logger.info("🔍 Alternative docs at /redoc")
    logger.info("")
    logger.info("🔐 Auth endpoints:")
    logger.info("   - POST /auth/register - Create new account")
    logger.info("   - POST /auth/jwt/login - Login")
    logger.info("   - POST /auth/jwt/logout - Logout")
    logger.info("   - GET /users/me - Get current user")
    logger.info("")
    logger.info("👑 Admin panel:")
    logger.info("   - GET /admin/panel - Admin dashboard (HTML)")
    logger.info("   - GET /admin/users - List all users (JSON)")
    logger.info("   - PATCH /admin/users/{id}/approve - Approve user")
    logger.info("   - PATCH /admin/users/{id}/revoke - Revoke user access")
    logger.info("   - DELETE /admin/users/{id} - Delete user")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Legal Document Processor API",
        "version": "3.0.0",
        "framework": "FastAPI",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Async/await for better performance",
            "Automatic API documentation",
            "Type validation with Pydantic",
            "Modern Python async/await patterns",
            "State Machine workflow architecture"
        ],
        "endpoints": {
            "process": "POST /process/sm - Document processing with State Machine",
            "workflow_map": "GET /workflow/map - View complete workflow",
            "workflow_viz": "GET /workflow/visualize - ASCII visualization"
        }
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
