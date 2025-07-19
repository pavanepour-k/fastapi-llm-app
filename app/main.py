"""
Main FastAPI application with all components integrated
Reference: https://fastapi.tiangolo.com/tutorial/bigger-applications/
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

from app.shared.config import settings
from app.shared.database import sessionmanager
from app.shared.cache import cache_manager
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.chat.websocket import websocket_router
from app.rag.router import router as rag_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown operations.
    
    Single Responsibility: Application lifecycle management
    """
    # Startup
    print("Starting up application...")
    await sessionmanager.init_db()
    await cache_manager.connect()
    print("Application startup complete")
    
    yield
    
    # Shutdown
    print("Shutting down application...")
    await sessionmanager.close()
    await cache_manager.disconnect()
    print("Application shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"] if settings.debug else ["localhost"]
)

# CORS middleware for development
if settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Single Responsibility: Health status reporting
    """
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment
    }


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve main application page.
    
    Single Responsibility: Main page serving
    """
    return templates.TemplateResponse(
        "chat/index.html", 
        {"request": request, "app_name": settings.app_name}
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """
    Custom 404 page handler.
    
    Single Responsibility: 404 error handling
    """
    return templates.TemplateResponse(
        "errors/404.html", 
        {"request": request}, 
        status_code=404
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
