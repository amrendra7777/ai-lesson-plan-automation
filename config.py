"""
config.py — Centralized configuration for the Lesson Plan Automation Pipeline.
Loads settings from .env and exposes constants used across all modules.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini API ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# -- Groq API (fallback, free at console.groq.com) --------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Pipeline Defaults ──────────────────────────────────────────────────────────
LANGUAGE: str = os.getenv("LANGUAGE", "Português Brasileiro")

# ── Test Mode ──────────────────────────────────────────────────────────────────
TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"
UNIT_COUNT: int = 4 if TEST_MODE else 20

# ── Temperature Settings per Agent ─────────────────────────────────────────────
ARCHITECT_TEMP: float = 0.2
DRAFTER_TEMP: float = 0.7
QA_TEMP: float = 0.3

# ── Output ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "output")
