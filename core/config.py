"""
config.py
---------
Loads all environment variables from .env and exposes them
as simple constants used across the whole project.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq (Agent 1 — Question Generator) ──────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Gemini (Agent 2 — Evaluator) ─────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "results.db")

# ── Evaluator Server ──────────────────────────────────────────────────────────
EVALUATOR_HOST: str = os.getenv("EVALUATOR_HOST", "127.0.0.1")
EVALUATOR_PORT: int = int(os.getenv("EVALUATOR_PORT", "8000"))
EVALUATOR_URL: str = f"http://{EVALUATOR_HOST}:{EVALUATOR_PORT}/evaluate"

# ── Validation — fail early if keys are missing ───────────────────────────────
def validate_config() -> None:
    """Raise an error immediately if any required API key is missing."""
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please add them to your .env file."
        )
