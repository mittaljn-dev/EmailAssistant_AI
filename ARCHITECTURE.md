# ARCHITECTURE.md — System Design

## CAP 942 Capstone | AI Email Assistant

---

## 1. High-Level Overview

The application has three layers:

```
┌─────────────────────────────────────────────┐
│           PRESENTATION LAYER                │
│              app.py                         │
│         Streamlit Web UI                    │
│  (what the user sees and interacts with)    │
└──────────────┬──────────────────────────────┘
               │ calls
               ▼
┌──────────────────────────────────────────────┐
│            LOGIC LAYER                       │
│   llm_engine.py      vector_store.py         │
│   (AI processing)    (memory/search)         │
└──────────┬───────────────────┬───────────────┘
           │ calls             │ calls
           ▼                   ▼
┌──────────────────┐  ┌─────────────────────────┐
│  EXTERNAL LAYER  │  │     DATA LAYER           │
│  Ollama Server   │  │  ChromaDB (disk)         │
│  Llama 3.2:1b    │  │  data/chroma_db/         │
└──────────────────┘  └─────────────────────────┘
```

---

## 2. Component Roles

### `app.py` — Presentation Layer

- Entry point. Run with: `uv run streamlit run app.py`
- Manages all UI: sidebar, pages, text inputs, buttons, output display
- Calls llm_engine for AI processing
- Calls vector_store for saving and searching
- Handles streaming output (shows tokens as they arrive)
- Does NOT contain any business logic or AI logic

### `src/email_assistant/config.py` — Configuration

- Single source of truth for ALL settings
- No logic, only constants and path definitions
- Every other module imports from here
- Change the model or settings in ONE place

### `src/email_assistant/llm_engine.py` — AI Logic Layer

- Builds prompts for each feature
- Sends prompts to Ollama via the `ollama` Python library
- Uses streaming mode (yields chunks, not full response at once)
- Returns generators that app.py consumes token by token
- Contains: check_ollama_connection(), rewrite_email(),
  summarize_email(), extract_action_items(), improve_clarity()

### `src/email_assistant/vector_store.py` — Memory Layer

- Manages ChromaDB connection (embedded, no server needed)
- Uses SentenceTransformers to convert text → 384-dimension vectors
- Uses @lru_cache so the embedding model loads only once
- Contains: save_email(), search_emails(), get_all_emails(),
  delete_all_emails(), collection_count()

---

## 3. Data Flow — Step by Step

### When a user rewrites an email

```
Step 1: User pastes email text into Streamlit text area
        app.py captures the text as a Python string

Step 2: User clicks "Rewrite Professionally" button
        app.py calls llm_engine.rewrite_email(text)

Step 3: llm_engine builds a prompt:
        "You are a professional email assistant.
         Rewrite this email: [user's text]"

Step 4: llm_engine calls ollama.chat(model, prompt, stream=True)
        Ollama loads Llama 3.2:1b into RAM (if not already loaded)
        Model starts generating tokens one by one

Step 5: Each token streams back to app.py
        app.py appends each token to the display
        User sees the response being typed out in real time

Step 6: When streaming finishes, app.py has the full response
        app.py calls vector_store.save_email(original, result, "rewrite")

Step 7: vector_store encodes the text using SentenceTransformers
        Produces a 384-dimension vector (list of 384 numbers)

Step 8: vector_store stores the vector + text + metadata in ChromaDB
        ChromaDB writes to disk at data/chroma_db/
        A unique UUID is assigned to this record
```

### When a user searches history

```
Step 1: User types a search query e.g. "meeting rescheduled"
        app.py captures the query string

Step 2: app.py calls vector_store.search_emails("meeting rescheduled")

Step 3: vector_store encodes the query using SentenceTransformers
        Produces a 384-dimension query vector

Step 4: ChromaDB compares the query vector against all stored vectors
        using cosine distance (mathematical similarity measurement)

Step 5: ChromaDB returns the top-4 most similar records
        Each result includes: document text, metadata, distance score

Step 6: app.py converts distance to similarity percentage
        Displays results ranked by relevance
```

---

## 4. Why Streaming Matters

Without streaming (blocking mode):

```
User clicks button → [spinner for 30-60 seconds] → full response appears
```

With streaming (our approach):

```
User clicks button → tokens appear word by word → feels like live typing
```

On an 8 GB RAM machine with CPU inference, generation takes 15-45 seconds.
Streaming makes this feel interactive instead of frozen.

---

## 5. Why @lru_cache on the Embedding Model

Loading SentenceTransformers from disk takes ~3-4 seconds.
Without caching:

```
save_email() call 1 → load model (3s) → encode → store
save_email() call 2 → load model (3s) → encode → store  ← wasteful!
save_email() call 3 → load model (3s) → encode → store  ← wasteful!
```

With @lru_cache:

```
save_email() call 1 → load model (3s) → encode → store
save_email() call 2 → model already in memory → encode → store  ✅
save_email() call 3 → model already in memory → encode → store  ✅
```

The model loads once per session and stays in memory — saving 3 seconds
on every subsequent call.

---

## 6. RAM Budget (8 GB Machine)

| Component | RAM Usage |
|------------|-----------|
| Windows 10/11 + background apps | ~2.5 GB |
| Ollama + Llama 3.2:1b model | ~1.3 GB |
| SentenceTransformers (all-MiniLM-L6-v2) | ~90 MB |
| ChromaDB (in-process) | ~50 MB |
| Streamlit UI | ~150 MB |
| Python runtime + libraries | ~200 MB |
| **Total used** | **~4.3 GB** |
| **Free headroom** | **~3.7 GB** ✅ |

---

## 7. File Structure Reference

```
EmailAssistant_AI/
│
├── app.py                      ← Entry point (Streamlit UI)
├── pyproject.toml              ← Dependencies and project config
├── uv.lock                     ← Exact locked versions of all packages
├── .python-version             ← Python version pin for uv
│
├── src/
│   └── email_assistant/
│       ├── __init__.py         ← Makes this folder a Python package
│       ├── config.py           ← All settings (model, paths, options)
│       ├── llm_engine.py       ← Ollama API calls + prompt engineering
│       └── vector_store.py     ← ChromaDB operations + embeddings
│
├── tests/
│   ├── __init__.py
│   └── test_vector_store.py    ← pytest unit tests
│
├── data/
│   └── chroma_db/              ← Auto-created by ChromaDB on first run
│
├── assets/
│   └── workflow_diagram.png    ← Architecture diagram (added later)
│
├── docs/
│   ├── proposal.md             ← Project proposal document
│   └── final_documentation.md ← Final capstone documentation
│
├── PLAN.md                     ← Thinking and decisions
├── ARCHITECTURE.md             ← This file
└── README.md                   ← Setup and usage instructions
```
