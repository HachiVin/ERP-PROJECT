"""Static configuration: paths, companies, session-state keys, and AI defaults."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AI_LOGS_DIR = BASE_DIR / "ai_logs"

APP_TITLE = "ERP Dashboard"

# Company name -> Streamlit page that shows its dashboard (None = page not built yet).
COMPANIES: dict[str, str | None] = {
    "FisTx": "pages/dashboard_fistx.py",
    "Maximus": None,
    "MSMB": None,
    "Widya Life Science": None,
    "Widya Genomic": None,
    "Sandhiguna": None,
    "Robotic": None,
    "BCK": None,
    "Widya Analytic": None,
    "Lectro": None,
    "SEIA": None,
}
FISTX_DATA_DIR = DATA_DIR / "fistx"

# --- Streamlit session-state keys ----------------------------------------------------
STATE_LOGGED_IN = "logged_in"
STATE_USERNAME = "username"
STATE_AI_SUGGESTIONS = "ai_suggestions"
STATE_AI_OWNER = "ai_owner"  # username that STATE_AI_SUGGESTIONS was loaded for
STATE_SELECTED_MODULE = "selected_module"
DEFAULT_MODULE = "CRM"

# --- AI insight (OpenRouter) ---------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-20b:free"
# OpenRouter's router that picks any currently available free model.
FREE_ROUTER_MODEL = "openrouter/free"

# The LLM only sees this many rows from the top of each table (a deliberate PoC scope).
AI_SAMPLE_ROWS = 5
AI_MAX_WORDS = 120
AI_TIMEOUT_SECONDS = 60.0
AI_SYSTEM_PROMPT = "You are an AI assistant for ERP data analysis."
