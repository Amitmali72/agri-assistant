"""
Configuration module for KrishiMitra — Voice-First Multilingual Agricultural Assistant.
Loads settings from .env file (if present) and falls back to environment variables and defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (agri_assistant directory)
_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")


class Settings:
    # ── Application & Security ───────────────────────────────────────────────
    APP_NAME: str = "KrishiMitra"
    APP_VERSION: str = "2.0.0"
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "krishimitra-admin-2026")
    AUDIO_RETENTION_HOURS: int = int(os.getenv("AUDIO_RETENTION_HOURS", "24"))

    # ── Ollama / Hosted LLM ──────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_CONNECT_TIMEOUT: float = float(os.getenv("LLM_CONNECT_TIMEOUT", "2.0"))
    LLM_READ_TIMEOUT: float = float(os.getenv("LLM_READ_TIMEOUT", "45.0"))

    # ── Speech-to-Text (Whisper) ─────────────────────────────────────────────
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    STT_CONFIDENCE_THRESHOLD: float = float(os.getenv("STT_CONFIDENCE_THRESHOLD", "0.35"))

    # ── Embeddings & Retrieval ───────────────────────────────────────────────
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    MAX_CHUNKS: int = int(os.getenv("MAX_CHUNKS", "5"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.28"))

    # ── Storage Paths ────────────────────────────────────────────────────────
    BASE_DIR: Path = _BASE_DIR
    VECTOR_STORE_PATH: str = os.getenv(
        "VECTOR_STORE_PATH",
        str(_BASE_DIR / "vector_store"),
    )
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        str(_BASE_DIR / "agri_assistant.db"),
    )
    FRONTEND_DIST_DIR: str = os.getenv(
        "FRONTEND_DIST_DIR",
        str(_BASE_DIR / "frontend-web" / "dist"),
    )

    # ── Text-to-Speech ───────────────────────────────────────────────────────
    # Options: "gtts" (free) or "bhashini" (Indian govt TTS API)
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "gtts")
    BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")
    BHASHINI_USER_ID: str = os.getenv("BHASHINI_USER_ID", "")

    # ── WhatsApp Business Cloud API (optional) ───────────────────────────────
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "agri_assistant_webhook_verify_token")

    # ── Live Agricultural Data APIs ──────────────────────────────────────────
    AGMARKNET_API_KEY: str = os.getenv("AGMARKNET_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    WEATHER_CACHE_TTL_SECONDS: int = int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "900"))
    MANDI_CACHE_TTL_SECONDS: int = int(os.getenv("MANDI_CACHE_TTL_SECONDS", "1800"))

    # ── Server ───────────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))

    def __repr__(self) -> str:
        return (
            f"Settings(APP_VERSION={self.APP_VERSION!r}, "
            f"OLLAMA_MODEL={self.OLLAMA_MODEL!r}, "
            f"WHISPER_MODEL={self.WHISPER_MODEL!r}, "
            f"TTS_PROVIDER={self.TTS_PROVIDER!r})"
        )


settings = Settings()
