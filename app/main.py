"""
Main entry point for the Legal Document Intelligence API.
Initializes FastAPI app with lifespan, routers, rate limiting,
and global exception handlers.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from dotenv import load_dotenv

#-------Imports from other packages---------
from logs.logger import get_logger
from app.routers.ingestion import ingestion_router
from app.routers.documents import document_router
from app.routers.retrieval import retrieval_router
from app.routers.auth import auth_router
from app.utils.mongo import connect as mongo_connect, disconnect as mongo_disconnect, get_user_session_mapping
from app.utils.checkpointer import load_checkpointer
from app.utils.pinecone_vdb import connect as pinecone_connect
from app.utils.embeddings import load_model
from app.utils.rerank import load_rerank_model
from evaluation.mlflow_logger import init_mlflow, register_prompts

load_dotenv()
logger = get_logger()
VERSION = os.getenv("API_VERSION", "v1")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages app startup and shutdown lifecycle.
    Startup: connects to databases and loads ML models.
    Shutdown: disconnects from MongoDB.
    """
    try:
        logger.info("Starting up Legal RAG API...")
        mongo_connect()
        get_user_session_mapping().create_index(
            [("email", 1), ("sessions.session_id", 1)],
            unique=True
        )
        app.state.checkpointer  = load_checkpointer()
        pinecone_connect(os.getenv("PINECONE_INDEX_NAME"))
        load_model()
        load_rerank_model()
        init_mlflow()
        register_prompts()
        logger.info("All models and connections initialized!")
        yield
        logger.info("Shutting down Legal RAG API...")
        mongo_disconnect()
        logger.info("Shutdown complete!")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise RuntimeError(f"Startup failed: {e}")

app = FastAPI(
    title="Legal Document Intelligence API",
    description="RAG system for legal document analysis",
    version=os.getenv("APP_VERSION","1.0.0"),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)

#---------Exception Handlers-----------
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handles all RuntimeError exceptions globally."""
    logger.error(f"RuntimeError: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handles all ValueError exceptions globally."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc)}
    )

#---------Routers-----------
app.include_router(ingestion_router,prefix=f"/api/{VERSION}/ingestion")
app.include_router(document_router, prefix=f"/api/{VERSION}/document")
app.include_router(retrieval_router, prefix=f"/api/{VERSION}/retrieval")
app.include_router(auth_router, prefix=f"/api/{VERSION}/auth")

#---------Health Check-----------
@app.get(f"/api/{VERSION}/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint to verify API is running.
    :return: dict with status message
    """
    return {"status": "healthy", "message": "Sarbo Mangalo Shanti"}