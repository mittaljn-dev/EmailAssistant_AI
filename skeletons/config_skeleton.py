"""
config.py — Skeleton & Structure Guide
=======================================
Central configuration for the AI Email Assistant.

This file has ONE job: store all settings in one place.
No logic. No functions. Just constants and path definitions.

WHY CONFIG.PY EXISTS
────────────────────
Without config.py — settings scattered everywhere:
    llm_engine.py    → model = "llama3.2:1b"
    vector_store.py  → model = "all-MiniLM-L6-v2"
    app.py           → title = "AI Email Assistant"
    ...

    To change the AI model, you'd hunt through EVERY file ❌

With config.py — ONE place to change everything:
    config.py        → OLLAMA_MODEL = "llama3.2:1b"
    all other files  → from .config import OLLAMA_MODEL

    To change the model: edit ONE line in config.py ✅

FILE STRUCTURE
──────────────
config.py
│
├── IMPORTS
│   └── pathlib.Path    ← smart cross-platform file paths
│
├── PATH SETTINGS
│   ├── BASE_DIR        ← project root folder (auto-detected)
│   └── CHROMA_DIR      ← where ChromaDB saves its files
│
├── OLLAMA SETTINGS
│   ├── OLLAMA_MODEL    ← which AI model to use
│   └── OLLAMA_OPTIONS  ← RAM and speed tuning
│
├── EMBEDDING SETTINGS
│   └── EMBED_MODEL     ← which embedding model to use
│
├── CHROMADB SETTINGS
│   └── COLLECTION_NAME ← name of our database "table"
│
└── UI SETTINGS
    ├── APP_TITLE       ← browser tab title
    ├── APP_ICON        ← browser tab icon
    ├── MAX_HISTORY     ← max emails in history tab
    └── SEARCH_TOP_K    ← max search results
"""

from pathlib import Path

# ─────────────────────────────────────────────────────────────
# CONCEPT: PATHLIB.PATH
# ─────────────────────────────────────────────────────────────
# Path() is Python's built-in smart path handler.
# Better than plain strings because it works on Windows, Mac, Linux.
#
# Plain string (fragile):
#   "C:\\Projects\\EmailAssistant_AI\\data"  ← Windows only ❌
#   "/home/user/EmailAssistant_AI/data"      ← Mac/Linux only ❌
#
# Path() (works everywhere):
#   Path("/home/user/project") / "data"      ← cross-platform ✅
#   The / operator joins path segments smartly

# ─────────────────────────────────────────────────────────────
# CONCEPT: RESOLVING BASE_DIR
# ─────────────────────────────────────────────────────────────
# We need to find the project root folder from inside config.py.
# config.py lives at: ProjectRoot/src/email_assistant/config.py
#
# Path(__file__)                  → config.py itself
# Path(__file__).resolve()        → absolute path, no ambiguity
# Path(__file__).resolve().parent → email_assistant/ folder
# .parent.parent                  → src/ folder
# .parent.parent.parent           → ProjectRoot/ ← what we want
#
# This works no matter where you run the app from.
# Always resolves to the project root correctly.

# ─────────────────────────────────────────────────────────────
# PATH SETTINGS
# ─────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Result: C:\Projects\EmailAssistant_AI\  (on your machine)

CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
# Result: C:\Projects\EmailAssistant_AI\data\chroma_db\

# mkdir() creates the folder if it doesn't exist yet.
# parents=True  → also create parent folders if needed
# exist_ok=True → don't raise an error if folder already exists
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# OLLAMA MODEL SETTINGS
# ─────────────────────────────────────────────────────────────

# WHY llama3.2:1b FOR 8 GB RAM:
#   llama3.2:1b → 1B parameters → ~1.3 GB RAM ✅ fits easily
#   llama3.2:3b → 3B parameters → ~2.5 GB RAM ✅ richer but slower
#   llama3      → 8B parameters → ~5.0 GB RAM ❌ too heavy, causes swapping
#
# To upgrade: change to "llama3.2:3b" then run: ollama pull llama3.2:3b
OLLAMA_MODEL = "llama3.2:1b"

# OLLAMA PERFORMANCE OPTIONS
# These are sent directly to Ollama with every request.
OLLAMA_OPTIONS = {

    # temperature: controls creativity vs consistency
    #   0.0 = fully deterministic (same input → same output always)
    #   1.0 = very creative and varied
    #   0.3 = slightly creative but mostly consistent ← good for email tasks
    "temperature": 0.3,

    # num_predict: maximum tokens in the response
    #   512 tokens ≈ roughly 350-400 words
    #   Lower = faster. Raise to 768 if outputs feel cut off.
    "num_predict": 512,

    # num_ctx: context window size (how much text model can "see")
    #   2048 = model reads up to ~1500 words of input at once
    #   IMPORTANT FOR 8 GB RAM: don't raise above 2048
    #   The context window lives in RAM — bigger = more RAM used
    "num_ctx": 2048,

    # num_thread: CPU cores used for inference
    #   4 is safe for most laptops
    #   Raise to match your CPU core count for faster responses
    "num_thread": 4,
}


# ─────────────────────────────────────────────────────────────
# EMBEDDING MODEL SETTINGS
# ─────────────────────────────────────────────────────────────

# WHY all-MiniLM-L6-v2:
#   Only ~90 MB model size (tiny vs LLMs)
#   Runs on CPU with no GPU needed
#   Fast encoding (~50ms per email)
#   Produces 384-dimension vectors
#   High quality semantic similarity scores
EMBED_MODEL = "all-MiniLM-L6-v2"


# ─────────────────────────────────────────────────────────────
# CHROMADB SETTINGS
# ─────────────────────────────────────────────────────────────

# The "collection" in ChromaDB is like a table in SQL.
# All our saved emails go into this one collection.
COLLECTION_NAME = "email_history"


# ─────────────────────────────────────────────────────────────
# UI SETTINGS
# ─────────────────────────────────────────────────────────────

APP_TITLE    = "AI Email Assistant"  # browser tab title
APP_ICON     = "✉️"                  # browser tab icon

MAX_HISTORY  = 50    # max emails shown in "All Emails" tab at once
                     # prevents UI from getting slow with large history

SEARCH_TOP_K = 4     # number of results returned from semantic search
                     # higher = more results but slower query
