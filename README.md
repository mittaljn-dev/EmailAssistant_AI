# ✉️ AI Email Assistant

## CAP 942 — Capstone Project | AI Application Development

> A fully local AI email assistant powered by **Llama 3.2 (1B)** via Ollama.
> No paid APIs. No internet needed at runtime. Runs on **8 GB RAM**.

How many of us have sent an email we immediately wished we could rewrite?
Or received a long message and thought — *I just need the key points from this.*
That is exactly the problem this app solves.

The AI Email Assistant rewrites, summarizes, extracts action items, replies,
translates, and searches your past emails — all running privately on your own
machine, with no subscriptions, no data leaving your device, and no cost.

---

## What It Does

| Feature | Description |
| ------- | ----------- |
| ✍️ Rewrite | Turns a casual draft into a professional email |
| 📋 Summarize | Compresses long emails into 3-5 bullet points |
| ✅ Extract | Pulls out tasks, deadlines, names, and decisions |
| 💡 Improve Clarity | Coaching feedback plus an improved version |
| ↩️ Reply Email | Drafts a professional reply to any incoming email |
| 🌐 Translate Email | Auto-detects language and translates to/from English or 19 other languages |
| 🗂️ Search History | Finds past emails by meaning using vector search |

---

## Tech Stack

| Layer | Tool |
| ----- | ---- |
| AI Model | Llama 3.2:1b via Ollama (local, free) |
| UI | Streamlit |
| Vector Database | ChromaDB (embedded) |
| Embeddings | all-MiniLM-L6-v2 (SentenceTransformers) |
| Package Manager | uv |
| Language | Python 3.10+ |

---

## Requirements

- Windows 10/11, Mac, or Linux
- Python 3.10 or higher
- 8 GB RAM minimum
- [uv](https://docs.astral.sh/uv/) installed
- [Ollama](https://ollama.com) installed

---

## Installation

### 1. Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Ollama and pull the model

Download Ollama from <https://ollama.com> then run:

```bash
ollama pull llama3.2:1b
```

### 3. Clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/EmailAssistant_AI.git
cd EmailAssistant_AI
```

### 4. Install dependencies

```bash
uv sync
```

### 5. Run the app

```bash
# Terminal 1 — start Ollama
ollama serve

# Terminal 2 — start the app
uv run streamlit run app.py
```

Open your browser at **<http://localhost:8501>**

---

## Project Documentation

| File | Description |
| ---- | ----------- |
| [PLAN.md](PLAN.md) | Problem thinking and design decisions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and data flow |
| [docs/proposal.md](docs/proposal.md) | Capstone project proposal |
| [docs/final_documentation.md](docs/final_documentation.md) | Final documentation |

---

## No paid APIs. Runs 100% on your local machine
