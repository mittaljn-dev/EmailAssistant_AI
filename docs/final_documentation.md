# Final Documentation — AI Email Assistant
## CAP 942: Capstone Project — AI Application Development

**Student Name:** Mittal Jain
**Date:** [03/2026]
**GitHub:** https://github.com/mittal-jn/EmailAssistant_AI

---

## 1. Application Overview

### Purpose
The AI Email Assistant is a locally-run Streamlit web application
that uses Llama 3.2:1b via Ollama to help office professionals
and business workers manage and improve their email communication.

### Problem It Solves
- Poor writing quality in quickly drafted emails
- Time lost reading long complex messages
- Tasks and deadlines missed because they are buried in email text
- No easy way to draft a professional reply to a complex incoming email
- Language barriers when communicating with international contacts
- No way to find past emails by their meaning

### Intended Users
Office professionals and business workers who write and receive
emails daily. The application is designed to be simple enough
for any professional to use without technical knowledge.

### Key Design Decisions
- **Local only** — no data ever leaves the user's machine
- **No subscriptions** — entirely free and open source
- **Low RAM** — runs on 8 GB machines using Llama 3.2:1b
- **Streaming output** — responses appear word by word so
  the interface feels fast even on CPU inference

---

## 2. Technical Workflow Diagram
```
┌─────────────────────────────────────────────────────────┐
│                        USER                             │
│              Pastes email text into UI                  │
│           Selects feature from sidebar                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              STREAMLIT UI  (app.py)                     │
│                                                         │
│  ✍️ Rewrite  📋 Summarize  ✅ Extract  💡 Clarity        │
│       ↩️ Reply  🌐 Translate  🗂️ Search History          │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐  ┌───────────────────────────┐
│    llm_engine.py         │  │    vector_store.py         │
│                          │  │                            │
│  1. Builds prompt        │  │  1. Loads embed model      │
│  2. Calls Ollama API     │  │     (cached with lru_cache)│
│  3. Streams tokens back  │  │  2. Encodes text → vector  │
│                          │  │  3. Stores in ChromaDB     │
└──────────┬───────────────┘  └──────────────┬────────────┘
           │                                 │
           ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────────┐
│  Ollama Server       │      │  ChromaDB                 │
│  (localhost:11434)   │      │  (data/chroma_db/)        │
│                      │      │                           │
│  Llama 3.2:1b model  │      │  Persistent vector store  │
│  CPU inference       │      │  384-dimension embeddings │
│  ~1.3 GB RAM         │      │  Survives app restarts    │
└──────────┬───────────┘      └──────────────┬────────────┘
           │                                 │
           │  tokens stream back             │ semantic search
           ▼                                 ▼
┌─────────────────────────────────────────────────────────┐
│              STREAMLIT UI — Output                      │
│                                                         │
│  Result streams live word by word                       │
│  Full text saved to ChromaDB automatically             │
│  Search history finds emails by meaning                 │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Tools, Libraries and Frameworks

| Tool | Version | Role |
|------|---------|------|
| Python | 3.14.3 | Programming language |
| uv | 0.10+ | Package manager and virtual environment |
| Ollama | 0.4+ | Local LLM server runner |
| Llama 3.2:1b | — | Open-source language model |
| Streamlit | 1.40+ | Web UI framework |
| ChromaDB | 0.5+ | Embedded vector database |
| SentenceTransformers | 3.0+ | Text embedding model loader |
| all-MiniLM-L6-v2 | — | Embedding model (~90 MB) |
| pytest | 9.0+ | Unit testing framework |
| ruff | 0.6+ | Python linter |

---

## 4. Application Architecture

### File Structure
```
EmailAssistant_AI/
│
├── app.py                    ← Entry point, Streamlit UI
├── pyproject.toml            ← uv project config
│
├── src/email_assistant/
│   ├── __init__.py           ← Python package marker
│   ├── config.py             ← All settings, one place
│   ├── llm_engine.py         ← Ollama calls and prompts
│   └── vector_store.py       ← ChromaDB operations
│
├── tests/
│   └── test_vector_store.py  ← 13 pytest unit tests
│
├── data/chroma_db/           ← Auto-created by ChromaDB
├── docs/                     ← Proposal and documentation
├── PLAN.md                   ← Design thinking
└── ARCHITECTURE.md           ← System design reference
```

### Component Responsibilities

**`config.py`** — Single source of truth for all settings.
Model name, RAM options, file paths, and UI constants all
live here. Every other file imports from config.py instead
of hardcoding values.

**`llm_engine.py`** — All AI logic. Builds prompts for each
feature, sends them to Ollama using `stream=True`, and yields
tokens back one at a time as a Python generator. Contains
`check_ollama_connection()` which verifies the server is
running before the app accepts any user input. Functions:
`rewrite_email()`, `summarize_email()`, `extract_action_items()`,
`improve_clarity()`, `generate_reply_email()`,
`detect_and_translate()`, `translate_to_language()`.

**`vector_store.py`** — All memory logic. Uses `@lru_cache`
to load the SentenceTransformers model once per session.
Separates embedding text (500 chars for speed) from stored
text (full length for display). Provides save, search,
retrieve, and delete operations over ChromaDB.

**`app.py`** — Presentation only. No business logic lives
here. Uses a dispatch table (PAGE_MAP dictionary) to route
between pages. Uses `st.empty()` placeholders to render
streaming output token by token.

### Data Flow — Rewrite Feature Example
```
1. User pastes email → captured as Python string
2. Button clicked → llm_engine.rewrite_email(text) called
3. Prompt built: "Rewrite this email professionally..."
4. ollama.chat(stream=True) called → generator returned
5. Each token yielded → appended to placeholder display
6. Streaming complete → full response in memory
7. vector_store.save_email(original, result, "rewrite")
8. SentenceTransformers encodes combined text → 384 numbers
9. ChromaDB stores vector + full text + metadata to disk
10. User sees complete result + "💾 Saved to history"
```

---

## 5. Features and Functionality

### Rewrite Email
Transforms casual or poorly written drafts into professional
communication. The prompt instructs the model to fix grammar
and tone while preserving the original meaning. Output
appears via streaming so users see results immediately.

### Summarize Email
Compresses long messages into 3-5 bullet points each starting
with the • character. The model is instructed to be concise
with a maximum of one sentence per bullet point. Useful for
long thread summaries and management updates.

### Extract Action Items
Produces four structured sections from any email — ACTION
ITEMS, DEADLINES, PEOPLE, and DECISIONS OR REQUESTS. The
model uses ALL CAPS section headers in the prompt which
improves structured output consistency in small 1B models.

### Improve Clarity
Provides two outputs in one response — a FEEDBACK section
with 2-3 sentences of coaching on tone, clarity, and
structure, followed by an IMPROVED VERSION of the email.
Acts as an on-demand writing coach.

### Reply Email

Reads an incoming email and drafts a complete professional
reply including a subject line and body. The prompt instructs
the model to answer any questions directly, keep the tone
actionable, and output only the reply with no commentary.
Result saved to ChromaDB with action="reply".

### Translate Email
Two modes on one page. **Translate to English** auto-detects
the source language using the model and outputs a structured
response with DETECTED LANGUAGE label followed by the full
English translation. **Translate to Language** accepts a
target language from a dropdown of 19 options (Spanish,
French, Arabic, Japanese, and more) and translates any email
into that language while preserving professional tone. Both
modes are saved to ChromaDB with action="translate".

### Search History
Every processed email is automatically saved to ChromaDB
with a 384-dimension vector embedding. Users can search
past emails using natural language queries. Results are
ranked by cosine similarity and displayed with a percentage
match score. Finds emails by meaning not exact keywords.

---

## 6. RAM Optimisation for 8 GB Machines

| Decision | RAM Saved | Reason |
|----------|-----------|--------|
| Llama 3.2:1b not llama3 | ~3.7 GB | 8B model needs 5 GB alone |
| num_ctx=2048 not 4096 | ~400 MB | Halves the KV cache size |
| num_predict=512 cap | Prevents runaway generation | Keeps responses fast |
| @lru_cache on embed model | ~300ms per call | Load once, reuse forever |
| ChromaDB embedded mode | ~200 MB | No separate server process |

Total RAM usage: approximately 4.3 GB leaving 3.7 GB headroom.

---

## 7. Challenges and Lessons Learned

### Challenge 1 — Understanding Vector Search
The hardest concept in this project was understanding how
semantic search works. The key insight was that text is
converted into a list of 384 numbers (a vector) where
similar meanings produce similar number patterns. ChromaDB
compares these patterns using cosine distance — measuring
the angle between vectors in 384-dimensional space. Once
this clicked, the implementation became straightforward.

### Challenge 2 — RAM Constraints
The obvious model choice llama3 (8B) caused heavy disk
swapping on an 8 GB machine making inference take several
minutes. Switching to llama3.2:1b (1B parameters, 1.3 GB)
brought inference down to 15-30 seconds per request on CPU
— a usable speed for interactive work.

### Challenge 3 — Streaming vs Blocking Output
Without streaming the UI appeared frozen for 30-60 seconds
after clicking a button. Implementing ollama.chat with
stream=True and using st.empty() placeholders gave the
response a live typing effect that makes the wait feel much
shorter even though total processing time is the same.

### Challenge 4 — Windows Encoding Issues
Python on Windows defaults to cp1252 encoding which could
not handle some Unicode characters in the CSS. Fixed by
setting PYTHONUTF8=1 as an environment variable and always
opening files with encoding='utf-8' explicitly.

### Challenge 5 — Git Tracking __pycache__
Python's bytecode cache folder was accidentally staged in
Git before .gitignore was created. Required git rm --cached
to stop tracking it. Lesson — create .gitignore before
writing any code.

### Key Lessons
- Start with the smallest model that works, scale up later
- Streaming is essential for AI application UX
- uv is dramatically faster than pip for dependency management
- @lru_cache is critical for any expensive object loaded at startup
- Document decisions as you make them — PLAN.md saved time later

---

## 8. Testing

13 unit tests written using pytest covering all vector store
operations. Tests use a fixture with autouse=True to ensure
a clean database state before and after each test providing
full test isolation.

**Test coverage:**
- Empty collection verification
- Single and multiple record saves
- UUID return value validation
- Search on empty and populated database
- Metadata structure validation
- Distance score range validation
- Record retrieval and count accuracy
- Delete operations including edge cases
- All four action types verified

**Run tests:**
```bash
uv run pytest tests/ -v -W ignore::DeprecationWarning
```

**Result:** 13 passed, 0 failed

---

## 9. Future Enhancements

The most valuable next feature would be **PDF email import**
using the pypdf library. This would allow users to drag and
drop email export files directly into the app instead of
copying and pasting text manually. Many email clients support
PDF export making this immediately practical for real users.

Other potential enhancements:
- Gmail API integration for direct inbox access
- Batch processing of multiple emails at once
- Model selector in the UI to switch between Llama versions
- Export results to .docx or .txt files

---

*This application satisfies all CAP 942 requirements: uses one
open-source LLM (Llama 3.2:1b), accepts user input, produces
LLM-generated output, runs as a Streamlit web app, uses a vector
database (ChromaDB), includes clear documentation, and requires
no paid APIs.*