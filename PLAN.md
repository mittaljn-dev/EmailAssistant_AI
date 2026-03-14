# PLAN.md — Project Thinking & Decisions

## CAP 942 Capstone | AI Email Assistant

---

## 1. The Problem I'm Solving

Professional email communication is something almost every working person
struggles with daily. Specific pain points:

- Emails written in a hurry come across as rude or unclear
- Long email threads bury the key information
- Action items and deadlines get lost in paragraphs of text
- There's no easy way to find what a past email was about

I want to build a tool that acts like a smart assistant sitting next to you
while you write and read emails.

---

## 2. Why AI for This Problem?

Traditional solutions (spell checkers, templates) only fix surface-level
problems. They can't:

- Understand the INTENT of a poorly written email
- Summarize meaning (not just shorten text)
- Extract structured information (tasks, names, dates) from unstructured text
- Search past emails by what they MEAN rather than exact keywords

Large Language Models (LLMs) can do all of these because they understand
natural language — not just pattern matching.

---

## 3. Why These Specific Tools?

### Why Ollama + Llama 3.2:1b?

- Free and open source — no API costs
- Runs locally — data never leaves my computer
- 1B parameter model fits in 8 GB RAM (8B models cause heavy disk swapping)
- Fast enough for interactive use on CPU

### Why Streamlit?

- Build a full web UI in pure Python
- No HTML/CSS/JavaScript knowledge needed
- Perfect for AI demos and prototypes
- Hot-reloads when you save code changes

### Why ChromaDB?

- Embedded mode — no separate server to run
- Stores email vectors persistently on disk
- Simple Python API — easy to learn
- Free and open source

### Why SentenceTransformers (all-MiniLM-L6-v2)?

- Only ~90 MB model size
- Runs on CPU with no GPU needed
- Fast encoding (~50ms per email)
- High quality semantic embeddings for search

### Why uv?

- 10-100x faster than pip
- Manages virtual environment automatically
- Single pyproject.toml replaces requirements.txt + setup.py
- Reproducible builds via uv.lock

---

## 4. What I Decided NOT to Do (and Why)

| Decision | Reason |
| -------- | ------ |
| No llama3 (8B model) | Too heavy for 8 GB RAM machines |
| No paid APIs (OpenAI, etc.) | Capstone requires free tools only |
| No PDF upload (yet) | Keeps scope small for Phase 1 |
| No user authentication | Single-user local app, not needed |
| No Docker | Adds complexity, not required |
| No cloud deployment | Local-first is the requirement |

---

## 5. The Five Features — My Reasoning

### Feature 1: Rewrite Email

The most common need. Someone writes a quick draft and wants it
to sound professional before sending.

- Input: rough draft text
- Output: polished professional version, same meaning

### Feature 2: Summarize Email

For long emails where you just need the key points fast.

- Input: long email text
- Output: 3-5 bullet points covering the main ideas

### Feature 3: Extract Action Items

Turns unstructured email text into structured task lists.

- Input: email with tasks, deadlines, names scattered throughout
- Output: organised sections — Tasks / Deadlines / People / Decisions

### Feature 4: Improve Clarity

Acts like a writing coach — explains what's wrong AND fixes it.

- Input: any email
- Output: feedback on tone/clarity + improved version

### Feature 5: Search History (Vector Search)

The most technically interesting feature. Uses ChromaDB to find
past emails by meaning, not keywords.

- Input: natural language search query
- Output: most semantically similar past emails ranked by relevance

---

## 6. How the Features Connect

Every feature (1-4) automatically saves its result to ChromaDB.
Feature 5 then searches across everything saved by features 1-4.
This means the app gets MORE useful the more you use it.

---

## 7. Risks and How I Handled Them

| Risk | Mitigation |
| ------ | ------------ |
| Model too slow on CPU | Use 1B model, enable streaming so UI feels alive |
| Out of memory errors | Cap num_ctx at 2048, num_predict at 512 |
| ChromaDB grows too large | Truncate stored text to 500 chars, limit history to 50 |
| Import errors between modules | Use src/ layout + uv's package installation |
| Ollama not running when app starts | Check connection on startup, show clear error message |

---

## 8. What I Would Add With More Time

- PDF email import (using pypdf)
- Batch processing multiple emails at once
- Export results to .txt or .docx
- Gmail API integration for direct email access
- Switch between multiple models from the UI
