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
from database import init_database

# Import FastAPI routers
from routes.health_routes_fastapi import router as health_router
from routes.auth_routes_fastapi import router as auth_router
from routes.cartorio_routes_fastapi import router as cartorio_router
from routes.process_routes_fastapi import router as process_router, set_clients
from routes.process_routes_sm import router as process_sm_router

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Initialize database
try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Initialize external clients
config.initialize_vision_client()
config.initialize_gemini_client()

# Set clients for process routes
set_clients(config.get_vision_client(), config.get_gemini_model())

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(cartorio_router)
app.include_router(process_router)
app.include_router(process_sm_router)  # New State Machine endpoint

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
    logger.info("🚀 FastAPI application started successfully!")
    logger.info("📚 API documentation available at /docs")
    logger.info("🔍 Alternative docs at /redoc")


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
            "State Machine workflow architecture (POST /process/sm)"
        ]
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
