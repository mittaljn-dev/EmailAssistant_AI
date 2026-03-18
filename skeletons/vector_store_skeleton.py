"""
vector_store.py — Skeleton & Structure Guide
============================================
Manages saving and searching emails using ChromaDB
and SentenceTransformers.

This file has ONE job: handle the memory system.
No UI. No AI calls. Just database operations.

FILE STRUCTURE
──────────────
vector_store.py
│
├── IMPORTS
│   ├── uuid          ← generates unique IDs for each record
│   ├── datetime      ← timestamps for metadata
│   ├── lru_cache     ← caches expensive objects in memory
│   ├── chromadb      ← vector database
│   └── SentenceTransformer ← converts text → vectors
│
├── PRIVATE SINGLETONS (loaded once, cached forever)
│   ├── _get_embed_model()   ← loads SentenceTransformers
│   └── _get_collection()    ← connects to ChromaDB
│
└── PUBLIC FUNCTIONS
    ├── save_email()          ← WRITE: encode + store
    ├── search_emails()       ← READ: semantic search
    ├── get_all_emails()      ← READ: retrieve all, newest first
    ├── delete_all_emails()   ← DELETE: clear everything
    └── collection_count()    ← COUNT: how many records
"""

from __future__ import annotations
import uuid
from datetime import datetime
from functools import lru_cache

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, SEARCH_TOP_K


# ─────────────────────────────────────────────────────────────
# CONCEPT 1: WHAT IS A VECTOR?
# ─────────────────────────────────────────────────────────────
# A vector is a list of numbers that represents meaning.
#
# When SentenceTransformers reads: "Please send the Q3 report"
# It converts it to: [0.231, -0.847, 0.123, 0.445, ...] ← 384 numbers
#
# These 384 numbers CAPTURE THE MEANING of the sentence.
# Similar sentences produce similar number patterns.
#
# ANALOGY — GPS coordinates for meaning:
#   "Send the Q3 report by Friday"     → coordinates near [0.23, -0.84]
#   "Submit quarterly report soon"     → coordinates very nearby ✅
#   "I love pizza"                     → coordinates very far away ❌

# ─────────────────────────────────────────────────────────────
# CONCEPT 2: WHAT IS COSINE DISTANCE?
# ─────────────────────────────────────────────────────────────
# When you search, ChromaDB measures how similar your query
# vector is to each stored vector using cosine distance.
#
# Imagine two arrows pointing in 384-dimensional space:
#   Small angle between them = similar meaning  ✅
#   Large angle between them = different meaning ❌
#
# Distance values:
#   0.0 = identical meaning
#   0.5 = somewhat related
#   1.0 = completely unrelated
#   2.0 = opposite meaning
#
# We convert to percentage in the UI:
#   similarity = (2 - distance) / 2 * 100
#   distance 0.2 → 90% similar ✅
#   distance 1.5 → 25% similar ❌

# ─────────────────────────────────────────────────────────────
# CONCEPT 3: WHAT IS @lru_cache?
# ─────────────────────────────────────────────────────────────
# lru_cache = Least Recently Used Cache
# A decorator that memorizes function results.
#
# WITHOUT cache — model loads every single call:
#   save_email() call 1 → load model (4 seconds) → encode → store
#   save_email() call 2 → load model (4 seconds) → encode → store ❌
#   save_email() call 3 → load model (4 seconds) → encode → store ❌
#
# WITH @lru_cache(maxsize=1) — loads once, reuses forever:
#   save_email() call 1 → load model (4 seconds) → encode → store
#   save_email() call 2 → already in memory (0 seconds) → encode ✅
#   save_email() call 3 → already in memory (0 seconds) → encode ✅
#
# maxsize=1 means: remember only the result of the last unique call.
# Since we always call it the same way, it effectively means
# "cache forever during this session."


# ─────────────────────────────────────────────────────────────
# PRIVATE SINGLETONS
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_embed_model() -> SentenceTransformer:
    """
    Loads the SentenceTransformer embedding model.
    Runs ONCE on first call. Result cached forever.

    WHY PRIVATE:
    Only functions INSIDE this file call this.
    app.py never interacts with the model directly.

    WHAT HAPPENS ON FIRST CALL:
        Downloads all-MiniLM-L6-v2 (~90 MB) if not cached
        Loads model into RAM
        lru_cache stores the result

    WHAT HAPPENS ON ALL FUTURE CALLS:
        lru_cache returns stored model instantly (0ms)
        No disk read. No RAM allocation. Just retrieval.

    MODEL CHOICE — why all-MiniLM-L6-v2:
        Only 90 MB (tiny compared to LLMs)
        Runs fast on CPU with no GPU needed
        Produces 384-dimension vectors
        High quality semantic similarity
    """
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _get_collection():
    """
    Initialises ChromaDB and returns our emails collection.
    Runs ONCE on first call. Connection cached forever.

    WHAT A COLLECTION IS:
    A ChromaDB collection is like a table in a regular database.
    All saved emails go into the "email_history" collection.

    PERSISTENTCLIENT vs CLIENT:
        chromadb.Client()           → data lost on app restart ❌
        chromadb.PersistentClient() → data saved to disk ✅
                                      survives app restarts

    GET OR CREATE PATTERN:
        get_or_create_collection()
            → if collection exists → opens it (loads existing data)
            → if not exists → creates fresh empty collection

    SETTINGS:
        anonymized_telemetry=False → ChromaDB won't send usage
                                     stats to their servers
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name=COLLECTION_NAME)


# ─────────────────────────────────────────────────────────────
# PUBLIC FUNCTIONS
# ─────────────────────────────────────────────────────────────

def save_email(original: str, processed: str, action: str) -> str:
    """
    Encodes and stores an email + its AI result in ChromaDB.

    PARAMETERS:
        original  → raw email text the user pasted
        processed → LLM output (rewrite/summary/extraction/clarity)
        action    → "rewrite" | "summarize" | "extract" | "clarity"

    RETURNS:
        str → UUID string assigned to this record
              e.g. "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    TWO-TEXT STRATEGY (important design decision):
        embed_text  = first 500 chars of original + processed
                      used ONLY for generating the vector
                      shorter = faster encoding

        combined    = FULL original + FULL processed
                      stored in ChromaDB for display
                      no truncation = user sees complete results

        WHY SEPARATE?
        Encoding 500 chars vs 5000 chars doesn't change search
        quality much — the meaning is captured in the first ~500 chars.
        But storing the full text means search results show everything.

    WHAT GETS STORED IN CHROMADB:
        ids        = [doc_id]      ← unique UUID string
        embeddings = [embedding]   ← list of 384 floats
        documents  = [combined]    ← full text for display
        metadatas  = [{            ← searchable extra info
            "action"   : "rewrite",
            "timestamp": "2024-03-14 09:30",
            "preview"  : first 120 chars of original
        }]

    NOTE: ChromaDB always expects LISTS even for single records.
    This is because it's designed for batch operations.
    """
    pass


def search_emails(query: str, top_k: int = SEARCH_TOP_K) -> list[dict]:
    """
    Finds past emails semantically similar to the query.

    HOW IT WORKS:
        1. Encode the query string into a 384-dimension vector
        2. ChromaDB compares that vector against ALL stored vectors
        3. Returns the top_k closest matches by cosine distance

    PARAMETERS:
        query  → natural language search string
                 e.g. "quarterly report deadline"
        top_k  → max results to return (default from config)

    RETURNS:
        list of dicts, each containing:
            "document"  → the stored text (original + result)
            "metadata"  → action, timestamp, preview
            "distance"  → cosine distance (lower = more similar)

        Returns [] if collection is empty (no emails saved yet)

    EDGE CASE HANDLING:
        count = collection.count()
        if count == 0: return []   ← can't search empty collection

        k = min(top_k, count)      ← can't return more than we have
                                      e.g. if only 2 emails saved,
                                      don't ask for top 4

    ZIP PATTERN (combining three parallel lists):
        results["documents"][0]  = [doc1, doc2, doc3]
        results["metadatas"][0]  = [meta1, meta2, meta3]
        results["distances"][0]  = [dist1, dist2, dist3]

        zip() combines them: [(doc1,meta1,dist1), (doc2,meta2,dist2)...]
    """
    pass


def get_all_emails(limit: int = 50) -> list[dict]:
    """
    Retrieves all saved emails sorted newest first.

    PARAMETERS:
        limit → max records to return (default 50)

    RETURNS:
        list of dicts with "document" and "metadata" keys
        sorted by timestamp string descending (newest first)

    SORT TRICK:
        ChromaDB doesn't support ORDER BY like SQL.
        We sort after fetching using Python's sort():
            pairs.sort(
                key=lambda x: x[1].get("timestamp", ""),
                reverse=True
            )
        This works because our timestamp format "YYYY-MM-DD HH:MM"
        sorts correctly as a plain string.
    """
    pass


def delete_all_emails() -> int:
    """
    Deletes every record from the collection.

    RETURNS:
        int → number of records deleted
              used to show "Deleted X records" in the UI

    PATTERN:
        1. Get count BEFORE deleting (to return it)
        2. Get all IDs (ChromaDB needs IDs to delete)
        3. collection.delete(ids=ids)
        4. Return the count

    EDGE CASE:
        if count == 0: return 0
        Don't try to delete from an empty collection.
    """
    pass


def collection_count() -> int:
    """
    Returns total number of saved emails.

    Used by:
        - Sidebar caption ("X emails in history")
        - search_emails() to prevent searching empty collection
        - Tests to verify save/delete operations worked

    One line: return _get_collection().count()
    """
    pass
