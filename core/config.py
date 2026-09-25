"""
config.py
---------
Configuration loader for the Adaptiq quiz platform.
Reads keys and settings from the .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI settings (Question generation)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or ""
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")

# Gemini settings (Evaluation & feedback)
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Local SQLite database path
DB_PATH: str = os.getenv("DB_PATH", "results.db")

# Optional evaluator service settings
EVALUATOR_HOST: str = os.getenv("EVALUATOR_HOST", "127.0.0.1")
EVALUATOR_PORT: int = int(os.getenv("EVALUATOR_PORT", "8000"))
EVALUATOR_URL: str = f"http://{EVALUATOR_HOST}:{EVALUATOR_PORT}/evaluate"


def validate_config() -> None:
    """Check that required API keys are available before starting."""
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:
        raise EnvironmentError(
            f"Missing required API key(s): {', '.join(missing)}. "
            "Please check your .env file."
        )
