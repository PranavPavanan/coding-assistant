"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import chat, health, indexing, repositories, search, websocket
from src.config import settings
from src.services.rag_service import get_rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - runs on startup and shutdown."""
    # Startup: Initialize RAG service with CodeLlama model
    print("\n" + "="*60)
    print("Starting RAG GitHub Assistant...")
    print("="*60)
    
    rag_service = get_rag_service(
        model_path=str(settings.get_model_path())
    )
    
    print(f"\nModel path: {settings.get_model_path()}")
    
    # Try to initialize the model
    if await rag_service.initialize():
        print("\nSUCCESS: RAG Service initialized successfully!")
        print("   CodeLlama model is ready for queries.")
    else:
        print("\nERROR: RAG Service initialization failed!")
        print("   Check the error messages above for details.")
        print("   Server will start but queries will return errors until fixed.")
    
    print("\n" + "="*60 + "\n")
    
    yield
    
    # Shutdown: Cleanup if needed
    print("\nShutting down RAG GitHub Assistant...")


app = FastAPI(
    title="RAG GitHub Assistant",
    version="0.1.0",
    description="RAG-powered GitHub repository code assistant",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(repositories.router, prefix="/api")
app.include_router(indexing.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# WebSocket endpoints (no prefix for WebSocket connections)
app.include_router(websocket.router)
