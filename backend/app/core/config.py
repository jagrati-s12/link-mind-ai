import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB_PATH = (_BACKEND_DIR / "linkmind.db").as_posix()

class Settings(BaseSettings):
    PROJECT_NAME: str = "LinkMind AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "linkmind-ai-insecure-dev-secret-key-change-in-prod-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Dual database support: SQLite default (anchored to backend dir), PostgreSQL if specified
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")
    
    # AI configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto") # auto, gemini, openai, heuristic
    
    # Upload and limits
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    MAX_UPLOAD_SIZE: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]
    REQUEST_TIMEOUT_SECONDS: int = 15
    MAX_SCRAPE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
