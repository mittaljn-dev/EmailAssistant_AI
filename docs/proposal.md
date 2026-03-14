# Project Proposal — AI Email Assistant
## CAP 942: Capstone Project — AI Application Development

**Student Name:** [Your Full Name]
**Date:** [Submission Date]
**Instructor:** [Instructor Name]

---

## 1. Problem Statement

Professional email communication is a daily challenge for office
professionals and business workers. Emails are often written quickly
under pressure, resulting in unclear language, unprofessional tone,
and missed action items. Studies show professionals spend over two
hours per day managing email — yet most have no tool to help them
write better or process incoming messages faster.

Three specific pain points drive this project:

1. **Poor writing quality** — rushed emails damage professional
   relationships and create misunderstandings
2. **Information overload** — key tasks and deadlines get buried
   in long email threads
3. **No meaningful search** — finding a past email requires
   remembering exact words, not just the topic

---

## 2. Why This Project Matters

Traditional tools like spell checkers and templates only fix
surface-level problems. They cannot understand the intent behind
poorly written text, summarize meaning from long messages, extract
structured information like tasks and deadlines from unstructured
paragraphs, or find past emails by what they mean rather than
what they literally say.

Large Language Models solve all of these problems because they
understand natural language at a deep level — not just pattern
matching. This project puts that capability directly in the hands
of office workers as a simple, private, free tool.

---

## 3. Proposed Solution

An AI-powered email assistant with five core features:

| Feature | AI Role |
|---------|---------|
| Rewrite Email | LLM rewrites draft in professional tone |
| Summarize Email | LLM produces 3–5 bullet point summary |
| Extract Action Items | LLM extracts tasks, deadlines, names |
| Improve Clarity | LLM provides coaching and improved version |
| Search History | Vector embeddings enable semantic search |

---

## 4. Target Users

**Primary users:** Office professionals and business workers who
write and receive emails daily as part of their core work activity.

**Specific use cases:**
- A manager reviewing a long project update email
- An employee drafting a difficult message to a client
- An assistant extracting tasks from a meeting follow-up email
- Anyone searching for a past conversation by topic

---

## 5. Tools and Frameworks

| Component | Technology | Reason for Choice |
|-----------|-----------|------------------|
| LLM | Llama 3.2:1b via Ollama | Free, local, fits 8 GB RAM |
| UI | Streamlit | Python-native, fast to build |
| Vector DB | ChromaDB embedded | No server needed, simple API |
| Embeddings | all-MiniLM-L6-v2 | Lightweight, 90 MB, CPU fast |
| Package manager | uv | Modern, fast, reproducible |
| Language | Python 3.14 | Industry standard for AI |

All tools are free and open source. No paid APIs are required.
The application runs entirely on a local machine with 8 GB RAM.

---

## 6. Expected Output and User Interaction

**User workflow:**
1. Open the Streamlit web UI at localhost:8501
2. Select a feature from the sidebar
3. Paste an email into the text box
4. Click the action button
5. Watch the AI response stream in real time
6. All results automatically saved to searchable history

**Sample input:**
```
hey sarah we need the q3 report done by friday also can u
tell the team to send their parts by thursday morning thx
```

**Expected rewrite output:**
```
Dear Sarah,

Please ensure the Q3 report is completed by Friday.
Could you also ask the team to submit their individual
contributions by Thursday morning?

Thank you.
```

---

## 7. Application Workflow

```
User Input (Streamlit UI)
        ↓
Feature Selection
(Rewrite / Summarize / Extract / Improve)
        ↓
Prompt Engineering (llm_engine.py)
        ↓
Ollama API → Llama 3.2:1b (local CPU)
        ↓
Streaming Response → Displayed token by token in UI
        ↓
SentenceTransformers → Text encoded as 384-dimension vector
        ↓
ChromaDB → Vector + full text stored persistently on disk
        ↓
Search History → Semantic query → Top-K results by similarity
```

---

## 8. Project Scope

**In scope for this capstone:**
- Single user local application
- Plain text email input
- Four AI processing features
- Vector-based semantic search history
- Streamlit web interface

**Out of scope (future work):**
- PDF email import
- Multi-user support
- Cloud deployment
- Email client integration

---

## 9. Timeline

| Week | Milestone |
|------|-----------|
| 1 | Research tools, install Ollama, uv, VS Code |
| 2 | Project structure, GitHub, pyproject.toml |
| 3 | Write config.py, llm_engine.py, vector_store.py |
| 4 | Write app.py, fix bugs, full integration testing |
| 5 | Write tests, proposal, final documentation, diagram |

---

*This project meets all CAP 942 minimum requirements: uses one
open-source LLM, accepts user input, produces LLM-generated output,
runs as a Streamlit web app, and includes a vector database for
retrieval features. No paid APIs are required.*