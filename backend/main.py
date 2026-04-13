from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from routes import artifacts, llm, parse, upload
from utils.file_handler import get_file_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PDF Parser Comparison System API")
    yield
    logger.info("Shutting down PDF Parser Comparison System API")


app = FastAPI(
    title="PDF Parser Comparison System",
    description="Backend API for comparing different PDF parsers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(llm.router)
app.include_router(parse.router)
app.include_router(artifacts.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "pdf-parser-comparison"}


@app.get("/files/{file_id}")
async def get_file(file_id: str):
    """Serve uploaded PDF file."""
    file_path = get_file_path(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PDF Parser Comparison System API",
        "docs": "/docs",
        "endpoints": {
            "upload": "/upload",
            "recommend": "/llm/recommend",
            "parse": "/parse",
        },
    }
