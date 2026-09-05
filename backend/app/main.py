from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.utils.logger import logger
from app.database.session import init_db
from app.api.routes import health, verification, claims, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down hallucination verification service.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Hybrid AI-Based System for Detecting and Verifying Hallucinated Information in Generative AI Responses",
    lifespan=lifespan
)

# Configure CORS for Chrome Extension & Dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time-Seconds"] = f"{process_time:.4f}"
    return response


import os
from fastapi.staticfiles import StaticFiles

# Include modular routers
app.include_router(health.router)
app.include_router(verification.router)
app.include_router(claims.router)
app.include_router(history.router)

# Mount Dashboard static assets
dashboard_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dashboard", "public"))
if os.path.isdir(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "health": "/api/health"
    }
