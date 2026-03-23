"""
llm_engine.py
─────────────
Handles all communication with Ollama (our local AI server).

This file contains:
- check_ollama_connection() : verify Ollama is running before use
- rewrite_email()           : rewrite a draft professionally
- summarize_email()         : summarize into bullet points
- extract_action_items()    : extract tasks, deadlines, names
- improve_clarity()         : coaching feedback + improved version

All feature functions return GENERATORS (they use yield, not return).
This enables streaming — Streamlit receives and displays tokens
one by one as the AI generates them, instead of waiting for the
full response.
"""

# Generator is a type hint — we use it to tell other developers
# (and our future self) that these functions return generators.
# It comes from Python's built-in typing module.
from typing import Generator

# This is the official Ollama Python library.
# It communicates with the Ollama server running on your machine
# at http://localhost:11434 (Ollama's default address).
import ollama

# We import our settings from config.py instead of hardcoding
# values like "llama3.2:1b" directly in this file.
# This way if we ever change the model, we only edit config.py.
from .config import OLLAMA_MODEL, OLLAMA_OPTIONS

# The dot in ".config" means "from the same package as this file"
# (src/email_assistant/). This is called a relative import.
# It's the correct way to import between files in the same package.


# ── Internal Helper ────────────────────────────────────────────

def _stream(prompt: str) -> Generator[str, None, None]:
    """
    Send a prompt to Ollama and yield text chunks as they arrive.

    This is a PRIVATE function (notice the underscore _ prefix).
    The underscore is a Python convention meaning:
    "this function is for internal use only — don't call it
    from outside this file."

    The public functions (rewrite_email, summarize_email, etc.)
    all call this function internally.

    Parameters:
        prompt : str — the full instruction text to send to the model

    Yields:
        str — one chunk of text at a time as Ollama generates it
    """

    # ollama.chat() sends a message to the Ollama server.
    # Think of it like texting the AI — you send a message,
    # it texts back (but token by token when stream=True).
    #
    # model    : which AI model to use (from config.py)
    # messages : a list of message objects. We always send one
    #            message with role="user" (as if we're asking it).
    #            role="assistant" would be the AI's own messages.
    # stream   : True = yield tokens one by one (streaming mode)
    # options  : performance settings from config.py
    #            (temperature, num_predict, num_ctx, num_thread)
    stream = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        options=OLLAMA_OPTIONS,
    )

    # Iterate over the stream — each `chunk` is one piece of
    # the response (usually 1-3 tokens / words).
    for chunk in stream:
        # chunk is a dictionary. The text content lives at:
        # chunk["message"]["content"]
        #
        # chunk["message"] is the message object
        # chunk["message"]["content"] is the actual text
        text = chunk["message"]["content"]

        # Only yield if there's actual text content.
        # Some chunks arrive empty (metadata only) — we skip those.
        if text:
            yield text


# ── Connection Check ───────────────────────────────────────────

def check_ollama_connection() -> tuple[bool, str]:
    """
    Verify that Ollama is running AND our model is available.

    We call this when the app starts. If Ollama isn't running,
    we show a helpful error message instead of a confusing crash.

    Returns:
        tuple[bool, str]:
            - (True,  "success message") if everything is fine
            - (False, "error message")   if something is wrong

    A tuple is just a pair of values returned together.
    We unpack it in app.py like: ok, msg = check_ollama_connection()
    """

    try:
        # ollama.list() asks the Ollama server: "what models do you have?"
        # If Ollama isn't running, this raises an exception immediately.
        models = ollama.list()

        # models is a dictionary. models["models"] is a list of
        # model objects. Each object has a "name" key.
        # We build a list of just the names using a list comprehension.
        # e.g. ["llama3.2:1b", "phi3:mini", ...]
        names = [m["model"] for m in models.get("models", [])]

        # Check if our model (from config.py) is in the list.
        # We use "in" to check for a partial match because Ollama
        # sometimes stores model names with extra tags like
        # "llama3.2:1b-instruct-q4_K_M" and we just want to
        # know if "llama3.2:1b" appears anywhere in any name.
        if not any(OLLAMA_MODEL in n for n in names):
            return False, (
                f"Model **{OLLAMA_MODEL}** not found in Ollama.\n\n"
                f"Run this command in a new terminal:\n"
                f"```\nollama pull {OLLAMA_MODEL}\n```"
            )

        # If we get here, Ollama is running AND the model exists.
        return True, f"✅ Connected — using `{OLLAMA_MODEL}`"

    except Exception as exc:
        # If ANY error occurs (connection refused, timeout, etc.)
        # we catch it here and return a helpful message.
        # We never let the app crash with a raw Python error.
        return False, (
            "❌ Cannot reach Ollama. Make sure it is running.\n\n"
            "Open a new terminal and run:\n"
            "```\nollama serve\n```\n\n"
            f"Technical detail: `{exc}`"
        )


# ── Feature Functions ──────────────────────────────────────────
# Each function below:
# 1. Takes the user's email text as input
# 2. Builds a carefully engineered prompt
# 3. Calls _stream(prompt) and returns the generator
#
# They all return Generator[str, None, None] which means:
# "a generator that yields strings, takes no send value,
#  and returns nothing when done"


def rewrite_email(text: str) -> Generator[str, None, None]:
    """
    Rewrite a casual or poorly written email professionally.

    Prompt design notes:
    - We tell the model its ROLE first ("You are a...")
    - We give ONE clear instruction ("Rewrite...")
    - We specify what to fix ("grammar and tone")
    - We add a constraint ("Keep the same meaning")
    - We specify the output format ("Output only the rewritten email")
      This last line is critical — without it, small models often
      add commentary like "Sure! Here's the rewritten version:"
      before the actual email, which we don't want.
    """
    prompt = (
        "You are a professional email writing assistant.\n"
        "Rewrite the email below so it is clear, polite, and professional.\n"
        "Fix grammar and tone. Keep the same meaning.\n"
        "Output only the rewritten email, nothing else.\n\n"
        f"Original email:\n{text}\n\n"
        "Rewritten email:"
    )
    return _stream(prompt)


def summarize_email(text: str) -> Generator[str, None, None]:
    """
    Summarize a long email into 3-5 bullet points.

    Prompt design notes:
    - We specify EXACTLY how many bullet points (3-5)
    - We tell it to start each bullet with "•" so the output
      is consistent and easy to parse/display
    - "Be concise" prevents the model from padding bullet points
      with unnecessary filler words
    """
    prompt = (
        "You are an email summarization assistant.\n"
        "Summarize the email below in 3-5 short bullet points.\n"
        "Start each bullet point with the character •\n"
        "Be concise. Each bullet should be one sentence maximum.\n\n"
        f"Email:\n{text}\n\n"
        "Summary:"
    )
    return _stream(prompt)


def extract_action_items(text: str) -> Generator[str, None, None]:
    """
    Extract structured information from an email.

    Prompt design notes:
    - We define FOUR specific sections to extract
    - We use ALL CAPS section headers — small models follow
      structured formatting instructions more reliably this way
    - "If a section is empty, write None" prevents the model
      from hallucinating (making up) action items that don't exist
    """
    prompt = (
        "You are an assistant that extracts key information from emails.\n"
        "From the email below, extract and list:\n\n"
        "ACTION ITEMS: (tasks that need to be done)\n"
        "DEADLINES: (any dates or time limits mentioned)\n"
        "PEOPLE: (names and their roles if mentioned)\n"
        "DECISIONS OR REQUESTS: (key asks or conclusions)\n\n"
        "If a section has nothing to report, write None.\n"
        "Use plain text only.\n\n"
        f"Email:\n{text}\n\n"
        "Extracted information:"
    )
    return _stream(prompt)


def improve_clarity(text: str) -> Generator[str, None, None]:
    """
    Provide coaching feedback and an improved version of an email.

    Prompt design notes:
    - We ask for TWO things: feedback AND improved version
    - We use clear section labels (FEEDBACK: / IMPROVED VERSION:)
      so the output is easy to read
    - "2-3 sentences" constrains the feedback length — without
      this, small models can go on forever with feedback
    """
    prompt = (
        "You are a professional communication coach.\n"
        "Review the email below and provide:\n\n"
        "FEEDBACK: (2-3 sentences on tone, clarity, and structure)\n"
        "IMPROVED VERSION: (a better rewritten version of the email)\n\n"
        f"Email:\n{text}\n\n"
        "Response:"
    )
    return _stream(prompt)

#translation function
def detect_and_translate(text: str) -> Generator[str, None, None]:
    """
    Auto-detects the language of the email and translates to English.
    Best used when receiving a foreign language email.

    Prompt design notes:
    - Asks model to first identify the language
    - Then translate to English
    - Output format is structured: DETECTED LANGUAGE + TRANSLATION
    - "Output nothing else" prevents model adding commentary
    """
    prompt = (
        "You are a professional language detection and translation assistant.\n"
        "Step 1: Identify the language of the email below.\n"
        "Step 2: If the email is already in English, respond with:\n"
        "DETECTED LANGUAGE: English\n"
        "NOTE: This email is already in English. No translation needed.\n"
        "Step 3: If the email is NOT in English, respond with:\n"
        "DETECTED LANGUAGE: [language name]\n"
        "TRANSLATION:\n[full English translation here]\n\n"
        "Do not add anything else.\n\n"
        f"Email:\n{text}\n\n"
        "DETECTED LANGUAGE:"
    )
    return _stream(prompt)


def translate_to_language(text: str, target_language: str) -> Generator[str, None, None]:
    """
    Translates an email from any language into the chosen target language.
    Best used when sending an email to someone who speaks another language.

    Prompt design notes:
    - Target language is injected directly into the prompt
    - "Professional email tone" preserves formality
    - "Output only the translated email" removes preamble
    - Works for all 8 supported languages
    """
    prompt = (
        f"You are a professional email translator.\n"
        f"Translate the email below into {target_language}.\n"
        f"Maintain a professional email tone.\n"
        f"Output only the translated email, nothing else.\n\n"
        f"Email:\n{text}\n\n"
        f"Translation in {target_language}:"
    )
    return _stream(prompt)