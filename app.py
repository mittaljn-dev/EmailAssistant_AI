"""
app.py
──────
Main entry point for the AI Email Assistant.

This is the only file the user interacts with directly.
It imports from llm_engine and vector_store and wires
everything together into a Streamlit web interface.

Run with:
    uv run streamlit run app.py
"""

# streamlit is our web UI framework.
# We import it as "st" — this is the universal convention.
# Every Streamlit function starts with st.
import streamlit as st

# Import all our feature functions from llm_engine.
# These all return generators (streaming text).
from src.email_assistant.llm_engine import (
    check_ollama_connection,
    rewrite_email,
    summarize_email,
    extract_action_items,
    improve_clarity,
)

# Import all our storage functions from vector_store.
from src.email_assistant.vector_store import (
    save_email,
    search_emails,
    get_all_emails,
    delete_all_emails,
    collection_count,
)

# Import UI settings from config.
from src.email_assistant.config import APP_TITLE, APP_ICON, OLLAMA_MODEL


# ── Page Configuration ─────────────────────────────────────────
# This MUST be the first Streamlit command in the file.
# It sets the browser tab title, icon, and layout.
# layout="wide" uses the full browser width instead of a narrow column.
# initial_sidebar_state="expanded" keeps sidebar open on load.
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom Styling ─────────────────────────────────────────────
# st.markdown() with unsafe_allow_html=True lets us inject
# raw HTML and CSS into the page.
# We use this to apply a custom dark theme with custom fonts.
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

   :root {
    --bg:      #1e2433;
    --surface: #262d40;
    --border:  #343d52;
    --accent:  #ff6b6b;
    --accent2: #4ecdc4;
    --text:    #eef0f4;
    --muted:   #7d8ba8;
    --success: #2dd4a0;
    --danger:  #ff4757;
  }

  html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
  }
  [data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }
  [data-testid="stSidebar"] * { color: var(--text) !important; }

  .main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    color: var(--text);
    letter-spacing: -0.5px;
  }
  .main-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    background: var(--accent);
    color: #0e0f11;
    padding: 3px 10px;
    border-radius: 4px;
    font-weight: 500;
    text-transform: uppercase;
    margin-left: 12px;
  }
  .main-sub {
    font-size: 0.9rem;
    color: var(--muted);
    margin-bottom: 28px;
  }
  .section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    color: var(--text);
    margin-bottom: 4px;
  }
  .section-sub {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 20px;
  }
  .result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    padding: 20px 24px;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.6;
    white-space: pre-wrap;
    color: var(--text);
    margin-top: 12px;
    max-height: 500px;
    overflow-y: auto;
  }
  .status-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 16px;
  }
  .dot-green { width:8px; height:8px; border-radius:50%;
               background:var(--success); flex-shrink:0; }
  .dot-red   { width:8px; height:8px; border-radius:50%;
               background:var(--danger);  flex-shrink:0; }
  .badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 8px;
    text-transform: uppercase;
    font-weight: 500;
  }
  .badge-rewrite   { background:#1e3a2f; color:var(--success); }
  .badge-summarize { background:#1a2d4a; color:var(--accent2); }
  .badge-extract   { background:#3a2a1a; color:#fb923c; }
  .badge-clarity   { background:#2d1a3a; color:#c084fc; }

  .stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.83rem !important;
  }
  .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(232,197,71,0.12) !important;
  }
  .stButton > button {
    background: var(--accent) !important;
    color: #0e0f11 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 26px !important;
    font-size: 0.88rem !important;
  }
  .stButton > button:hover { opacity: 0.85 !important; }
  .stTextInput input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
  }
  .stTextInput input:focus {
    border-color: var(--accent) !important;
  }
 #MainMenu, footer, header { visibility: hidden; }

 [data-testid="stExpander"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
  }
  [data-testid="stExpander"]:hover {
    border-color: var(--accent) !important;
  }
  [data-testid="stExpander"] summary {
    background-color: var(--surface) !important;
    color: var(--text) !important;
  }
  [data-testid="stExpander"] summary:hover {
    background-color: var(--surface) !important;
    color: var(--accent) !important;
  }
  [data-testid="stExpander"] summary:focus {
    background-color: var(--surface) !important;
  }

  [data-testid="stTabs"] button {
    color: var(--muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
  }
  [data-testid="stTabs"] button:hover {
    color: var(--text) !important;
    background-color: transparent !important;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--text) !important;
    font-weight: 600 !important;
  }
  [data-testid="stTabs"] [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important;
  }

 [data-testid="collapsedControl"] { display: none !important; }
 section[data-testid="stSidebar"] { 
    min-width: 300px !important; 
    width: 300px !important; 
    transform: none !important; 
}
  .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialisation ───────────────────────────────
# Session state persists between Streamlit reruns.
# We initialise keys here with defaults IF they don't exist yet.
# The "if not in" check prevents resetting state on every rerun.

# Which page is currently showing
if "page" not in st.session_state:
    st.session_state.page = "rewrite"

# Ollama connection status — checked once on startup
if "ollama_ok" not in st.session_state:
    ok, msg = check_ollama_connection()
    st.session_state.ollama_ok  = ok
    st.session_state.ollama_msg = msg


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    # App title in sidebar
    st.markdown("""
    <div style="padding:16px 0 20px 0">
      <div style="font-family:'DM Serif Display',serif;font-size:1.2rem;
                  color:#e2e4e9">✉ Email Assistant</div>
      <div style="font-family:'DM Mono',monospace;font-size:0.7rem;
                  color:#6b7280;margin-top:4px">CAP 942 · Capstone</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation buttons — one for each page.
    # When clicked, we update st.session_state.page and
    # Streamlit reruns the script, showing the new page.
    if st.button("✍️  Rewrite Email",       use_container_width=True):
        st.session_state.page = "rewrite"
    if st.button("📋  Summarize",            use_container_width=True):
        st.session_state.page = "summarize"
    if st.button("✅  Extract Action Items", use_container_width=True):
        st.session_state.page = "extract"
    if st.button("💡  Improve Clarity",      use_container_width=True):
        st.session_state.page = "clarity"
    if st.button("🗂️  Search History",       use_container_width=True):
        st.session_state.page = "history"

    st.divider()

    # Ollama status indicator — green dot if connected, red if not
    if st.session_state.ollama_ok:
        st.markdown(f"""
        <div class="status-bar">
          <div class="dot-green"></div>
          <span>Ollama · {OLLAMA_MODEL}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-bar">
          <div class="dot-red"></div>
          <span>Ollama offline</span>
        </div>""", unsafe_allow_html=True)
        # Show the helpful error message from check_ollama_connection()
        st.error(st.session_state.ollama_msg)

    # Show count of saved emails
    count = collection_count()
    st.caption(f"{count} email{'s' if count != 1 else ''} in history")

    # Button to re-check Ollama if user starts it after app loads
    if st.button("🔄 Recheck Ollama", use_container_width=True):
        ok, msg = check_ollama_connection()
        st.session_state.ollama_ok  = ok
        st.session_state.ollama_msg = msg
        st.rerun()  # force a full page refresh


# ── Main Header ────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:4px">
  <span class="main-title">AI Email Assistant</span>
  <span class="main-badge">Local · Private · Free</span>
</div>
<div class="main-sub">
  Rewrite · Summarize · Extract · Improve · Search — all on your machine.
</div>
""", unsafe_allow_html=True)


# ── Guard Function ─────────────────────────────────────────────
def _ollama_guard() -> bool:
    """
    Check if Ollama is ready before running any AI feature.
    Returns True if ready, False if not.
    Shows a helpful error message if not ready.

    We call this at the start of every feature page.
    This prevents confusing crashes if Ollama isn't running.
    """
    if not st.session_state.ollama_ok:
        st.error(
            "Ollama is not running. "
            "Open a new terminal and run `ollama serve` "
            "then click **Recheck Ollama** in the sidebar."
        )
        return False
    return True


# ── Helper: Run a Feature ──────────────────────────────────────
def _run_feature(text: str, generator_fn, action: str):
    """
    Generic function that handles the streaming + saving pattern.
    All four AI features (rewrite, summarize, extract, clarity)
    do the same thing:
      1. Call the LLM function (get a generator)
      2. Stream the output into a placeholder
      3. Save the result to ChromaDB

    Instead of copy-pasting this logic 4 times, we put it here
    and call it from each page. This is called DRY principle —
    Don't Repeat Yourself.

    Parameters:
        text         : the user's email input
        generator_fn : one of the llm_engine functions
        action       : "rewrite", "summarize", "extract", "clarity"
    """
    if not text.strip():
        st.warning("Please paste an email first.")
        return

    if not _ollama_guard():
        return

    # Create a placeholder — an empty spot on the page
    # that we will update repeatedly as tokens arrive
    placeholder = st.empty()
    full_response = ""

    # Call the LLM function — this returns a generator immediately
    # (no waiting) and starts streaming when we iterate it
    with st.spinner("Thinking..."):
        for chunk in generator_fn(text):
            full_response += chunk
            # Update the placeholder with everything received so far
            # The ▌ character is a fake cursor — gives the feeling
            # of the AI actively typing
            placeholder.markdown(
                f'<div class="result-card">{full_response}▌</div>',
                unsafe_allow_html=True,
            )

    # Streaming finished — remove the fake cursor
    placeholder.markdown(
        f'<div class="result-card">{full_response}</div>',
        unsafe_allow_html=True,
    )

    # Save to ChromaDB automatically after every feature
    save_email(text, full_response, action)
    st.success("💾 Saved to history.")


# ── Page Functions ─────────────────────────────────────────────
# Each page is its own function.
# The router at the bottom calls the right function based on
# st.session_state.page

def page_rewrite():
    st.markdown(
        '<div class="section-header">✍️ Rewrite Email</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Paste a casual draft — get a polished professional version.</div>',
        unsafe_allow_html=True
    )

    # Two columns — input left, output right
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("**Your Draft**")
        text = st.text_area(
            label="draft",
            label_visibility="collapsed",
            height=320,
            placeholder=(
                "e.g.  hey john we need the q3 report by friday "
                "also meeting got moved thx"
            ),
            key="rw_input",
        )
        run = st.button("✍️ Rewrite Professionally", key="rw_btn")

    with col2:
        st.markdown("**Professional Version**")
        # This placeholder lives permanently in col2
        # It gets filled when the button is clicked
        output_area = st.empty()
        # Show a waiting box before any result is generated
        output_area.markdown(
            '<div class="result-card" style="min-height:320px;'
            'display:flex;align-items:center;justify-content:center;'
            'color:#4a4d52;font-size:0.85rem;letter-spacing:0.5px;">'
            'Your rewritten email will appear here...'
            '</div>',
            unsafe_allow_html=True,
        )

    # Button logic runs AFTER both columns are defined
    # This is the key fix — we define columns first,
    # then handle the button click outside of them
    if run:
        if not text.strip():
            st.warning("Please paste an email first.")
        elif not _ollama_guard():
            pass
        else:
            full_response = ""
            with st.spinner(""):
                for chunk in rewrite_email(text):
                    full_response += chunk
                    output_area.markdown(
                        f'<div class="result-card">{full_response}▌</div>',
                        unsafe_allow_html=True,
                    )
            output_area.markdown(
                f'<div class="result-card">{full_response}</div>',
                unsafe_allow_html=True,
            )
            save_email(text, full_response, "rewrite")
            st.success("💾 Saved to history.")

def page_summarize():
    st.markdown(
        '<div class="section-header">📋 Summarize Email</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Turn long complex messages into 3–5 clear bullet points.</div>',
        unsafe_allow_html=True
    )
    text = st.text_area(
        label="email_sum",
        label_visibility="collapsed",
        height=240,
        placeholder="Paste a long email here...",
        key="sum_input",
    )
    if st.button("📋 Summarize Now", key="sum_btn"):
        _run_feature(text, summarize_email, "summarize")


def page_extract():
    st.markdown(
        '<div class="section-header">✅ Extract Action Items</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Find every task, deadline, person, and decision in an email.</div>',
        unsafe_allow_html=True
    )
    text = st.text_area(
        label="email_ext",
        label_visibility="collapsed",
        height=240,
        placeholder="Paste an email with tasks or deadlines...",
        key="ext_input",
    )
    if st.button("✅ Extract Now", key="ext_btn"):
        _run_feature(text, extract_action_items, "extract")


def page_clarity():
    st.markdown(
        '<div class="section-header">💡 Improve Clarity & Tone</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Get coaching feedback and an improved version in one shot.</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("**Your Email**")
        text = st.text_area(
            label="email_clar",
            label_visibility="collapsed",
            height=320,
            placeholder="Paste your email to get clarity coaching...",
            key="clar_input",
        )
        run = st.button("💡 Analyze & Improve", key="clar_btn")

    with col2:
        st.markdown("**Feedback & Improved Version**")
        output_area = st.empty()
        # Show a waiting box before any result is generated
        output_area.markdown(
            '<div class="result-card" style="min-height:320px;'
            'display:flex;align-items:center;justify-content:center;'
            'color:#4a4d52;font-size:0.85rem;letter-spacing:0.5px;">'
            'Your rewritten email will appear here...'
            '</div>',
            unsafe_allow_html=True,
        )

    if run:
        if not text.strip():
            st.warning("Please paste an email first.")
        elif not _ollama_guard():
            pass
        else:
            full_response = ""
            with st.spinner(""):
                for chunk in improve_clarity(text):
                    full_response += chunk
                    output_area.markdown(
                        f'<div class="result-card">{full_response}▌</div>',
                        unsafe_allow_html=True,
                    )
            output_area.markdown(
                f'<div class="result-card">{full_response}</div>',
                unsafe_allow_html=True,
            )
            save_email(text, full_response, "clarity")
            st.success("💾 Saved to history.")

def page_history():
    st.markdown(
        '<div class="section-header">🗂️ Search History</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-sub">Semantically search all past emails — finds meaning, not just keywords.</div>',
        unsafe_allow_html=True
    )

    # Badge HTML for each action type — coloured labels
    BADGES = {
        "rewrite"  : '<span class="badge badge-rewrite">rewrite</span>',
        "summarize": '<span class="badge badge-summarize">summarize</span>',
        "extract"  : '<span class="badge badge-extract">extract</span>',
        "clarity"  : '<span class="badge badge-clarity">clarity</span>',
    }

    # Three tabs inside the history page
    tab_search, tab_all, tab_manage = st.tabs([
        " Semantic Search",
        " All Emails",
        " Manage"
    ])

    with tab_search:
        query = st.text_input(
            "Search query",
            placeholder="e.g.  quarterly report,  meeting rescheduled...",
            key="search_q",
        )
        if st.button("🔍 Search", key="search_btn"):
            if not query.strip():
                st.warning("Enter a search term.")
            else:
                with st.spinner("Searching..."):
                    results = search_emails(query)

                if results:
                    st.success(f"Found **{len(results)}** result(s):")
                    for r in results:
                        # Convert cosine distance to similarity %
                        # distance 0.0 = 100% similar
                        # distance 2.0 = 0% similar
                        dist = r.get("distance", 0)
                        similarity = max(0, round((2 - dist) / 2 * 100, 1))
                        meta    = r["metadata"]
                        action  = meta.get("action", "")
                        ts      = meta.get("timestamp", "")
                        preview = meta.get("preview", "")
                        badge   = BADGES.get(action, "")

                        # st.expander creates a collapsible section
                        with st.expander(
                            f"[{similarity}% match]  {preview[:65]}"
                        ):
                            st.markdown(
                                f'<div style="font-family:DM Mono,monospace;'
                                f'font-size:0.72rem;color:#6b7280;margin-bottom:8px">'
                                f'{badge}{ts} · similarity {similarity}%</div>'
                                f'<div class="result-card">{r["document"]}</div>',
                                unsafe_allow_html=True,
                            )
                else:
                    st.info("No results found. Process some emails first!")

    with tab_all:
        all_emails = get_all_emails()
        st.caption(f"{len(all_emails)} email(s) saved")

        if all_emails:
            for item in all_emails:
                meta    = item["metadata"]
                action  = meta.get("action", "")
                ts      = meta.get("timestamp", "")
                preview = meta.get("preview", "")
                badge   = BADGES.get(action, "")

                with st.expander(f"{preview[:70]}"):
                    st.markdown(
                        f'<div style="font-family:DM Mono,monospace;'
                        f'font-size:0.72rem;color:#6b7280;margin-bottom:8px">'
                        f'{badge}{ts}</div>'
                        f'<div class="result-card">{item["document"]}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No emails saved yet. Use any feature above to get started!")

    with tab_manage:
        st.warning("Deleting history is permanent. All saved emails will be removed.")
        if st.button("🗑️ Delete All History", key="del_btn"):
            n = delete_all_emails()
            st.success(f"Deleted {n} record(s).")
            st.rerun()


# ── Page Router ────────────────────────────────────────────────
# This dictionary maps page names to their functions.
# Based on st.session_state.page, we call the right function.
#
# This pattern is called a "dispatch table" — instead of a
# long if/elif chain, we use a dictionary lookup.
#
# Long way (messy):
#   if st.session_state.page == "rewrite":   page_rewrite()
#   elif st.session_state.page == "summarize": page_summarize()
#   ...
#
# Clean way (dispatch table):
PAGE_MAP = {
    "rewrite"  : page_rewrite,
    "summarize": page_summarize,
    "extract"  : page_extract,
    "clarity"  : page_clarity,
    "history"  : page_history,
}

# Get the function for the current page and call it.
# If somehow the page name is invalid, default to page_rewrite.
PAGE_MAP.get(st.session_state.page, page_rewrite)()