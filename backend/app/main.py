import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import engine, Base
from app.api.v1 import (
    auth, sources, imports, resources, collections,
    skills, recommendations, applications, roadmaps,
    assistant, profile, stats, settings as user_settings
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkmind")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    logger.info("Initializing LinkMind database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LinkMind AI — Personal AI Learning & Opportunity Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend Vite development server & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(sources.router, prefix=settings.API_V1_STR)
app.include_router(imports.router, prefix=settings.API_V1_STR)
app.include_router(resources.router, prefix=settings.API_V1_STR)
app.include_router(collections.router, prefix=settings.API_V1_STR)
app.include_router(skills.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(roadmaps.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(profile.router, prefix=settings.API_V1_STR)
app.include_router(stats.router, prefix=settings.API_V1_STR)
app.include_router(user_settings.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": "1.0.0"}
