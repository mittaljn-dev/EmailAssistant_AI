"""
config.py
─────────
Central configuration for the Email Assistant.

All settings live here. Other files import from here.
If you want to change the model, RAM usage, or paths —
this is the ONLY file you need to edit.
"""

# pathlib is a built-in Python library for working with
# file and folder paths. It's smarter than plain strings
# because it works on Windows, Mac, and Linux automatically.
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
# Path(__file__) = the full path to THIS file (config.py)
# .resolve()     = converts to absolute path (no ../ ambiguity)
# .parent        = go up one folder (email_assistant/)
# .parent        = go up again (src/)
# .parent        = go up again (EmailAssistant_AI/) ← project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# This is where ChromaDB will store its files.
# BASE_DIR / "data" / "chroma_db" builds the path:
# C:\Projects\EmailAssistant_AI\data\chroma_db
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

# mkdir creates the folder if it doesn't exist yet.
# parents=True  → also creates parent folders if missing
# exist_ok=True → don't crash if folder already exists
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── Ollama Model ───────────────────────────────────────
# This is the AI model Ollama will use to process emails.
#
# WHY llama3.2:1b for 8 GB RAM?
#   llama3.2:1b  = 1 billion parameters = ~1.3 GB RAM  ✅
#   llama3.2:3b  = 3 billion parameters = ~2.5 GB RAM  ✅ (richer but slower)
#   llama3       = 8 billion parameters = ~5.0 GB RAM  ❌ too heavy for 8 GB
#
# To upgrade later: change "llama3.2:1b" to "llama3.2:3b"
# then run: ollama pull llama3.2:3b
OLLAMA_MODEL = "llama3.2:1b"


# ── Ollama Performance Options ─────────────────────────
# These settings tune how Ollama uses your RAM and CPU.
# All of these are passed directly to Ollama when we make a request.
OLLAMA_OPTIONS = {
    # temperature controls how "creative" vs "focused" the AI is.
    # 0.0 = fully deterministic (same input → same output always)
    # 1.0 = very creative and varied
    # 0.3 = slightly creative but mostly consistent — good for email tasks
    "temperature": 0.3,

    # num_predict = maximum number of tokens (words/pieces) in the response.
    # 512 tokens ≈ roughly 350-400 words — plenty for email tasks.
    # Lower = faster responses. Raise to 768 if outputs feel cut off.
    "num_predict": 512,

    # num_ctx = the context window size (how much text the model can "see").
    # 2048 = the model can read up to ~1500 words of input at once.
    # IMPORTANT for 8 GB RAM: don't raise this above 2048.
    # The context window lives in RAM — bigger = more RAM used.
    "num_ctx": 2048,

    # num_thread = how many CPU cores Ollama uses for inference.
    # 4 is a safe default for most laptops.
    # If you know your CPU has more cores, raise this for faster responses.
    "num_thread": 4,
}

# ── Embedding Model ────────────────────────────────────
# SentenceTransformers uses this model to convert text → vectors.
# "all-MiniLM-L6-v2" is only ~90 MB and runs fast on CPU.
# It's downloaded automatically the first time the app runs.
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── ChromaDB Settings ──────────────────────────────────
# The "collection" in ChromaDB is like a table in a regular database.
# All saved emails go into this collection.
COLLECTION_NAME = "email_history"

# ── UI Settings ────────────────────────────────────────
# These control the Streamlit interface appearance and behaviour.
APP_TITLE = "AI Email Assistant"
APP_ICON  = "✉️"

# How many past emails to show in the History tab at once.
MAX_HISTORY = 50

# How many search results to return when searching history.
SEARCH_TOP_K = 4




