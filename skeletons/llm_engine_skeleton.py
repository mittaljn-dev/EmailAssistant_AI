"""
llm_engine.py — Skeleton & Structure Guide
==========================================
Handles ALL communication with Ollama (local AI server).

This file has ONE job: talk to the AI and return responses.
No UI. No database. Just AI communication.

FILE STRUCTURE
──────────────
llm_engine.py
│
├── IMPORTS
│   ├── Generator (typing)      ← type hint for generator functions
│   ├── ollama                  ← Python client for Ollama server
│   └── config                  ← OLLAMA_MODEL, OLLAMA_OPTIONS
│
├── PRIVATE HELPER
│   └── _stream(prompt)         ← sends prompt, yields tokens
│       └── used by ALL feature functions below
│
├── CONNECTION CHECK
│   └── check_ollama_connection() ← verify server is running
│
└── FEATURE FUNCTIONS (all follow identical pattern)
    ├── rewrite_email(text)
    ├── summarize_email(text)
    ├── extract_action_items(text)
    └── improve_clarity(text)
"""

from typing import Generator
import ollama
from .config import OLLAMA_MODEL, OLLAMA_OPTIONS

# ─────────────────────────────────────────────────────────────
# CONCEPT 1: WHAT IS A GENERATOR?
# ─────────────────────────────────────────────────────────────
# A generator is a function that yields values one at a time
# instead of returning everything at once.
#
# Normal function — waits for everything, returns at once:
#   def get_response():
#       result = call_ai()   ← waits 30 seconds...
#       return result        ← returns everything at once
#
# Generator function — yields pieces as they arrive:
#   def get_response():
#       for chunk in call_ai():
#           yield chunk      ← sends each piece immediately
#
# ANALOGY:
#   Normal  = waiting for the WHOLE pizza before eating
#   Generator = eating each SLICE as it comes out of the oven
#
# In our app, Streamlit receives each token from the generator
# and displays it immediately. This is the "live typing" effect.

# ─────────────────────────────────────────────────────────────
# CONCEPT 2: WHAT IS STREAMING?
# ─────────────────────────────────────────────────────────────
# When ollama.chat() is called with stream=True, Ollama does NOT
# wait for the full response before sending anything back.
# Instead it sends tokens (word pieces) ONE BY ONE as generated.
#
# Without streaming:
#   [user clicks] → [frozen spinner 30-60 seconds] → [full text appears]
#
# With streaming:
#   [user clicks] → [text starts appearing after 2-3 seconds, word by word]
#
# Same total processing time — but streaming FEELS much faster
# because the user sees progress immediately.

# ─────────────────────────────────────────────────────────────
# CONCEPT 3: PROMPT ENGINEERING
# ─────────────────────────────────────────────────────────────
# The text you send to the model is called a "prompt".
# How you write the prompt dramatically affects output quality.
#
# For small 1B models, prompts need to be:
#   - SHORT       → fewer input tokens = faster processing
#   - DIRECTIVE   → tell it exactly what to output
#   - STRUCTURED  → specify the format you want back
#
# Bad prompt (too vague, model gets confused):
#   "Please consider this email and improve it professionally..."
#
# Good prompt (short, directive, format specified):
#   "Rewrite this email professionally.
#    Fix grammar and tone. Keep the same meaning.
#    Output only the rewritten email, nothing else.
#    Original: {text}
#    Rewritten email:"
#                   ↑ this ending tells the model WHERE to start writing
#                     called a "completion prompt"


# ─────────────────────────────────────────────────────────────
# PRIVATE HELPER
# ─────────────────────────────────────────────────────────────

def _stream(prompt: str) -> Generator[str, None, None]:
    """
    THE ENGINE ROOM — every feature function calls this.

    Leading underscore = private convention.
    Only functions INSIDE this file should call _stream().
    app.py never calls it directly.

    WHAT IT DOES:
        1. Sends prompt to Ollama via ollama.chat()
        2. stream=True → Ollama sends tokens one by one
        3. Loops over each arriving chunk
        4. Yields the text content of each chunk

    GENERATOR RETURN TYPE: Generator[str, None, None]
        str  → type of values yielded (text chunks)
        None → type of values sent in (we don't send anything)
        None → return type when generator is exhausted

    HOW OLLAMA.CHAT() WORKS:
        ollama.chat(
            model    = "llama3.2:1b",     ← which model to use
            messages = [                   ← conversation history
                {"role": "user", "content": prompt}
            ],
            stream   = True,              ← stream tokens back
            options  = {...}              ← RAM/speed settings
        )

    EACH CHUNK STRUCTURE:
        chunk["message"]["content"] → the text piece
        Some chunks arrive empty (metadata only) — we skip those
        with: if text: yield text
    """
    pass


# ─────────────────────────────────────────────────────────────
# CONNECTION CHECK
# ─────────────────────────────────────────────────────────────

def check_ollama_connection() -> tuple[bool, str]:
    """
    Verifies Ollama is running AND our model is available.
    Called ONCE when the app starts. Result stored in session_state.

    WHY IT EXISTS:
    Without this check, if Ollama isn't running and a user
    clicks a button, they get a confusing Python traceback.
    With this, we show a clear helpful message instead.

    RETURN TYPE: tuple[bool, str]
        (True,  "✅ Connected")      ← everything is fine
        (False, "❌ Run ollama serve") ← something is wrong

    UNPACKED IN app.py:
        ok, msg = check_ollama_connection()
        st.session_state.ollama_ok  = ok
        st.session_state.ollama_msg = msg

    LOGIC FLOW:
        try:
            ollama.list()              ← asks "what models do you have?"
            ↓ if Ollama not running → raises Exception → goes to except
            extract model names from response
            check if OLLAMA_MODEL is in the list
            ↓ if model missing → return (False, "pull this model...")
            return (True, "Connected!")
        except Exception as exc:
            return (False, "Run ollama serve...")
    """
    pass


# ─────────────────────────────────────────────────────────────
# FEATURE FUNCTIONS
# ─────────────────────────────────────────────────────────────
# ALL FOUR follow identical structure:
#   1. Build a short directive prompt
#   2. return _stream(prompt)
#
# The ONLY difference between them is the prompt text.
# Once you understand one, you understand all four.

def rewrite_email(text: str) -> Generator[str, None, None]:
    """
    Rewrites a casual email in a professional tone.

    PROMPT STRUCTURE:
        Role instruction  → "You are a professional email assistant."
        Task              → "Rewrite the email below..."
        Constraints       → "Fix grammar and tone. Keep the same meaning."
        Format instruction→ "Output only the rewritten email, nothing else."
        User input        → f"Original email:\n{text}"
        Completion cue    → "Rewritten email:"
                            ↑ model continues from here
    """
    pass


def summarize_email(text: str) -> Generator[str, None, None]:
    """
    Summarizes a long email into 3-5 bullet points.

    PROMPT DESIGN NOTES:
        - Specifies EXACTLY how many bullets (3-5)
        - Instructs model to start each with "•"
          → ensures consistent parseable output
        - "One sentence maximum" prevents padding
        - Small models follow specific format instructions
          much better than vague ones

    COMPLETION CUE: "Summary:"
    """
    pass


def extract_action_items(text: str) -> Generator[str, None, None]:
    """
    Extracts structured information from an email.

    PROMPT DESIGN NOTES:
        - Defines FOUR specific sections in ALL CAPS:
            ACTION ITEMS:
            DEADLINES:
            PEOPLE:
            DECISIONS OR REQUESTS:
        - ALL CAPS section headers work better with 1B models
          than markdown headers or numbered lists
        - "If a section is empty, write None" prevents
          hallucination (model making up tasks that don't exist)

    COMPLETION CUE: "Extracted information:"
    """
    pass


def improve_clarity(text: str) -> Generator[str, None, None]:
    """
    Provides coaching feedback AND an improved version.

    PROMPT DESIGN NOTES:
        - Asks for TWO outputs in one response:
            FEEDBACK:         ← 2-3 sentences of coaching
            IMPROVED VERSION: ← rewritten email
        - "2-3 sentences" constrains feedback length
          without this, small models can produce endless feedback
        - Clear section labels make output easy to read

    COMPLETION CUE: "Response:"
    """
    pass
