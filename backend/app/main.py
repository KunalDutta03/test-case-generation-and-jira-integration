"""
FastAPI main application entry point.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import documents, test_cases, jira, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.app_log_level, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and directories on startup."""
    logger.info("Starting TestOrbit backend...")
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Ensure directories exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.faiss_index_path).mkdir(parents=True, exist_ok=True)
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="TestOrbit — AI-Powered QA System",
    description="AI-powered Gherkin test case generation using Azure OpenAI GPT-4.1 with RAG pipeline",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(test_cases.router, prefix=API_PREFIX)
app.include_router(jira.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {
        "message": "TestOrbit Backend",
        "docs": "/api/docs",
        "version": "1.0.0",
    }
