"""
FastAPI Application Factory
Main entry point for the AI Research Agent API
"""
import sys
import os
from contextlib import asynccontextmanager

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from app.api import router as api_router
from app.chatbot_api import include_chatbot_routes
from config.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    settings = get_settings()
    logging.info(f"🚀 AI Research Agent API starting up...")
    logging.info(f"📡 Server running on {settings.host}:{settings.port}")
    logging.info(f"📚 API documentation available at http://{settings.host}:{settings.port}/docs")
    
    yield
    
    # Shutdown
    logging.info("🛑 AI Research Agent API shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    settings = get_settings()
    
    # Create FastAPI app with custom settings
    app = FastAPI(
        title="AI Research Agent API",
      
        version="1.0.0",
        contact={
            "name": "AI Research Agent Team",
            "email": "support@example.com",
        },
        license_info={
            "name": "MIT License",
        },
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware for security
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """
        Global exception handler for unhandled errors
        """
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint
        Returns the current status of the API
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "AI Research Agent API"
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """
        Root endpoint with API information
        """
        return {
            "message": "🔬 AI Research Agent API",
            "description": "Conversational research assistant powered by AI",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            
            "chatbot": {
                "start_chat": "/api/chatbot/chat/start",
                "send_message": "/api/chatbot/chat/message",
                "setup_project": "/api/chatbot/chat/setup-project",
                "generate_questions": "/api/chatbot/chat/generate-questions",
                "search_literature": "/api/chatbot/chat/search-literature",
                "analyze_gaps": "/api/chatbot/chat/analyze-gaps",
                "get_status": "/api/chatbot/chat/status/{session_id}",
                "export_framework": "/api/chatbot/chat/export/{session_id}",
                "health_check": "/api/chatbot/health"
            },
            "research": {
                "run_workflow": "/api/research/run",
                "generate_questions": "/api/research/questions",
                "analyze_project": "/api/research/analyze",
                "search_literature": "/api/research/literature",
                "database_info": "/api/database/info"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # Include chatbot routes
    include_chatbot_routes(app)
    
    # Include research API router with prefix
    app.include_router(
        api_router,
        prefix="/api",
        tags=["Research API"]
    )
    
    # Log registered routes (for debugging)
    @app.on_event("startup")
    async def log_routes():
        """Log all registered routes for debugging"""
        if settings.debug:
            routes_info = []
            for route in app.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    routes_info.append(f"{', '.join(route.methods)} {route.path}")
            
            logging.info("📋 Registered routes:")
            for route_info in sorted(routes_info):
                logging.info(f"  {route_info}")
    
    return app


# For development/testing - create app instance
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    settings = get_settings()
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
