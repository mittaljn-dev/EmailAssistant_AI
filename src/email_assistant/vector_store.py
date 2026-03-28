"""
vector_store.py
───────────────
Manages saving and searching emails using ChromaDB and
SentenceTransformers.

This file handles:
- save_email()        : encode text as vector and store in ChromaDB
- search_emails()     : find similar emails using semantic search
- get_all_emails()    : retrieve all saved emails newest first
- delete_all_emails() : clear all history
- collection_count()  : how many emails are saved
"""

# __future__ annotations lets us use type hints like list[dict]
# instead of List[Dict] (the older style). It's a modern Python
# feature that makes type hints cleaner to write.
from __future__ import annotations

# uuid generates unique IDs for each saved email.
# Every record in ChromaDB needs a unique string ID.
# uuid4() generates a random ID like: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
import uuid

# datetime lets us record when each email was processed.
# We store timestamps as strings like "2024-03-14 09:30"
from datetime import datetime

# lru_cache is the caching decorator explained in Concept 3 above.
# functools is Python's built-in utility functions module.
from functools import lru_cache

# chromadb is our vector database.
# PersistentClient means data is saved to disk (survives app restarts).
# Settings lets us configure ChromaDB behavior.
import chromadb
from chromadb.config import Settings

# SentenceTransformer is the model that converts text → vectors.
# We import just the class we need, not the entire library.
from sentence_transformers import SentenceTransformer

# Import our settings from config.py
# CHROMA_DIR    : the folder path where ChromaDB saves its files
# COLLECTION_NAME: the name of our "table" inside ChromaDB
# EMBED_MODEL   : "all-MiniLM-L6-v2" — the embedding model name
# SEARCH_TOP_K  : how many results to return (default 4)
from .config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, SEARCH_TOP_K


# ── Singleton Functions (load once, reuse forever) ─────────────

# @lru_cache(maxsize=1) means:
# "Run this function once, remember the result, and return that
#  same result on every future call without running the function again"
#
# This is critical for performance — SentenceTransformer takes
# 3-4 seconds to load from disk. We only want that cost once.
@lru_cache(maxsize=1)
def _get_embed_model() -> SentenceTransformer:
    """
    Load the SentenceTransformer embedding model.
    Called once on first use, then cached in memory.

    The leading underscore means this is private — only
    functions inside this file should call it directly.
    """
    # This downloads the model on first run (~90 MB).
    # After that it loads from your local cache folder.
    # On Windows: C:\Users\mitta\.cache\torch\sentence_transformers\
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _get_collection():
    """
    Initialize ChromaDB and return our emails collection.
    Called once on first use, then cached in memory.

    A ChromaDB "collection" is like a table in a regular database.
    get_or_create_collection means:
    - If the collection exists already → open it (load existing data)
    - If it doesn't exist yet → create a fresh empty one
    """
    # PersistentClient saves data to disk at CHROMA_DIR.
    # This means your email history survives app restarts.
    # Without PersistentClient (using Client() instead),
    # data would be lost every time you close the app.
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),  # ChromaDB needs a string, not a Path object
        settings=Settings(
            # Disable telemetry — ChromaDB by default sends anonymous
            # usage stats. We turn this off for privacy.
            anonymized_telemetry=False
        ),
    )

    # Get or create the collection named "email_history"
    return client.get_or_create_collection(name=COLLECTION_NAME)


# ── Public Functions ───────────────────────────────────────────

def save_email(original: str, processed: str, action: str) -> str:
    """
    Save a processed email to ChromaDB.

    How it works:
    1. Combines original + processed text into one string
    2. Encodes that string into a 384-number vector
    3. Stores the vector + text + metadata in ChromaDB
    4. Returns the unique ID assigned to this record

    Parameters:
        original  : the raw email text the user pasted
        processed : the LLM's output (rewrite/summary/etc.)
        action    : what was done — "rewrite", "summarize",
                    "extract", or "clarity"

    Returns:
        str : a UUID string like "f47ac10b-58cc-4372-..."
    """
    # Get our cached model and collection
    model      = _get_embed_model()
    collection = _get_collection()

    # We truncate to 500 characters before storing.
    # Reasons:
    # 1. Keeps the database file small
    # 2. Encoding is faster on shorter text
    # 3. 500 chars captures the essential meaning of any email

    # For EMBEDDING — we use only 500 chars for speed
    # Shorter text = faster encoding, smaller vectors
    embed_snippet = original[:500]
    embed_processed = processed[:500]
    embed_text = (
        f"[{action.upper()}]\n"
        f"Original: {embed_snippet}\n"
        f"Result: {embed_processed}"
    )

    # Combine both texts into one document string.
    # We store both the original and processed version together
    # so search results show the complete context.
    combined = (
        f"[{action.upper()}]\n"
        f"Original: {original}\n"
        f"Result: {processed}"
    )

    # encode() converts the text string into a vector.
    # convert_to_numpy=True returns a numpy array.
    # .tolist() converts it to a plain Python list because
    # ChromaDB expects a plain list, not a numpy array.
    # The result is a list of 384 floating point numbers.
    embedding = model.encode(embed_text, convert_to_numpy=True).tolist()

    # Generate a unique ID for this record.
    # str(uuid.uuid4()) gives us something like:
    # "550e8400-e29b-41d4-a716-446655440000"
    doc_id = str(uuid.uuid4())

    # collection.add() stores everything in ChromaDB.
    # Note: ALL parameters are lists (even for one item).
    # ChromaDB is designed to add multiple records at once,
    # so it always expects lists.
    collection.add(
        ids=[doc_id],           # unique identifier(s)
        embeddings=[embedding], # vector(s) — the 384 numbers
        documents=[combined],   # the actual text to store
        metadatas=[{            # extra info stored alongside
            "action"   : action,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "preview"  : original[:120].replace("\n", " "),
            # preview is the first 120 chars for display in the UI
            # replace("\n", " ") keeps it on one line for clean display
        }],
    )

    return doc_id


def search_emails(query: str, top_k: int = SEARCH_TOP_K) -> list[dict]:
    """
    Search past emails using semantic similarity.

    How it works:
    1. Encodes the search query into a 384-number vector
    2. ChromaDB compares this vector against ALL stored vectors
    3. Returns the top_k most similar records ranked by distance

    Parameters:
        query : natural language search string
                e.g. "quarterly report deadline"
        top_k : how many results to return (default from config.py)

    Returns:
        list of dicts, each with keys:
        - "document" : the stored text
        - "metadata" : action, timestamp, preview
        - "distance" : cosine distance (lower = more similar)

    Returns [] if no emails are saved yet.
    """
    collection = _get_collection()
    model = _get_embed_model()

    # Encode the search query the same way we encoded saved emails.
    # This puts the query in the same "vector space" so comparison works.
    embedding = model.encode(query, convert_to_numpy=True).tolist()

    # collection.query() is ChromaDB's search function.
    # ChromaDB handles empty collections and n_results > count gracefully —
    # no pre-flight count() call is needed.
    # query_embeddings : the vector to compare against
    # n_results        : how many matches to return
    # include          : what data to include in results
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"][0]:
        return []

    # results is a nested dictionary. Each value is a list of lists
    # because ChromaDB supports batch queries.
    # results["documents"][0] = documents for query 0 (our only query)
    # results["documents"][0][0] = first document of query 0
    #
    # We zip() the three lists together to process them in parallel.
    # zip([a1,a2], [b1,b2], [c1,c2]) → [(a1,b1,c1), (a2,b2,c2)]
    out = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        out.append({
            "document": doc,
            "metadata": meta,
            "distance": round(dist, 4),
            # round to 4 decimal places for clean display
        })

    return out


def get_all_emails(limit: int = 50) -> list[dict]:
    """
    Retrieve all saved emails, newest first.

    Parameters:
        limit : maximum records to return (default 50)

    Returns:
        list of dicts with "document" and "metadata" keys
        sorted newest → oldest by timestamp
    """
    collection = _get_collection()

    # collection.get() retrieves records without any search.
    # include tells ChromaDB what data to return.
    results = collection.get(
        include=["documents", "metadatas"]
    )

    if not results["documents"]:
        return []

    # Zip documents and metadata together into pairs
    # then sort by timestamp string newest first.
    # Timestamp format "YYYY-MM-DD HH:MM" sorts correctly
    # as a plain string because of the date format we chose.
    pairs = list(zip(results["documents"], results["metadatas"]))
    pairs.sort(
        key=lambda x: x[1].get("timestamp", ""),
        reverse=True  # newest first
    )

    # Return only up to `limit` records
    return [
        {"document": doc, "metadata": meta}
        for doc, meta in pairs[:limit]
    ]


def delete_all_emails() -> int:
    """
    Delete every record from the collection.

    Returns:
        int : the number of records that were deleted
    """
    collection = _get_collection()

    # Fetch only IDs — no need for documents or metadata.
    # include=[] returns just the ids list with no extra data fetched.
    ids = collection.get(include=[])["ids"]

    if not ids:
        return 0

    collection.delete(ids=ids)
    return len(ids)


def collection_count() -> int:
    """
    Return the total number of saved emails.
    Used by the sidebar to show the email count.
    """
    return _get_collection().count()