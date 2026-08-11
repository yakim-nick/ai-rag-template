"""RAG Playground — a Streamlit UI for the RAG service."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from rag import build_engine

# Module-level constant — can be reassigned for testing
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Extensions accepted by the uploader and indexed by the engine.
# Order matters: it drives the file-picker filter in the uploader.
ALLOWED_EXTENSIONS = (".pdf", ".md", ".txt", ".csv")

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RAG Playground",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ───────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine_refresh" not in st.session_state:
    st.session_state.engine_refresh = 0


# ── Engine (cached, keyed by refresh counter) ───────────────────────────────

@st.cache_resource
def get_engine(_refresh: int) -> object | None:
    """Build the RAG query engine.  Returns ``None`` on failure.

    ``_refresh`` is only used as a cache key: bumping
    ``st.session_state.engine_refresh`` after a file upload forces a rebuild
    so the new document gets indexed.
    """
    try:
        return build_engine(str(DATA_DIR))
    except Exception:
        return None


engine = get_engine(st.session_state.engine_refresh)


# ── Styling ─────────────────────────────────────────────────────────────────

def _inject_custom_css() -> None:
    """Inject the app's custom CSS (header banner, sidebar, chat styling)."""
    st.markdown(
        """
<style>
    /* ── Chat container ── */
    .main .block-container {
        max-width: 860px;
        padding: 1.5rem 1rem;
    }

    /* ── Header banner ── */
    .rag-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 60%, #3b7bb5 100%);
        padding: 2rem 2.5rem;
        border-radius: 18px;
        color: #fff;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    .rag-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .rag-header p {
        margin: 0.5rem 0 0;
        opacity: 0.88;
        font-size: 1.1rem;
    }

    /* ── Sidebar branding ── */
    .sidebar-brand {
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .sidebar-brand h2 {
        margin: 0;
        color: #1e3a5f;
        font-size: 1.5rem;
    }
    .sidebar-brand p {
        margin: 0.2rem 0 0;
        font-size: 0.8rem;
        color: #6b7280;
    }

    /* ── Chat messages ── */
    .stChatMessage {
        border-radius: 14px;
        padding: 0.25rem 0;
    }

    /* ── File uploader ── */
    section[data-testid="stFileUploader"] label {
        font-weight: 600;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #6b7280 !important;
    }

    /* ── Spinner ── */
    .stSpinner {
        margin: 1rem 0;
    }

    /* ── Responsive tweaks ── */
    @media (max-width: 640px) {
        .rag-header { padding: 1.2rem; }
        .rag-header h1 { font-size: 1.5rem; }
    }
</style>
""",
        unsafe_allow_html=True,
    )


# ── Helpers ─────────────────────────────────────────────────────────────────

def _list_documents() -> list[Path]:
    """Return non-hidden files from the data directory, sorted by name."""
    if not DATA_DIR.exists():
        return []
    return sorted(
        f for f in DATA_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )


def _handle_upload(uploaded_file) -> None:
    """Save an uploaded file to the data directory and trigger a rebuild.

    The engine is cached by ``engine_refresh``, so incrementing it invalidates
    the cache and forces the next render to re-index the new document.
    """
    file_path = DATA_DIR / uploaded_file.name
    try:
        file_bytes = uploaded_file.getvalue()
        file_path.write_bytes(file_bytes)
        st.toast(f"Uploaded **{uploaded_file.name}**", icon="✅")
        st.session_state.engine_refresh += 1
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to save file: {exc}")


# ── Sidebar ─────────────────────────────────────────────────────────────────

def _render_branding() -> None:
    """Render the sidebar branding header."""
    st.markdown(
        '<div class="sidebar-brand">'
        "<h2>🔍 RAG Playground</h2>"
        "<p>Retrieval-Augmented Generation</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_uploader() -> None:
    """Render the file uploader and handle a newly uploaded file."""
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=[ext.lstrip(".") for ext in ALLOWED_EXTENSIONS],
        accept_multiple_files=False,
    )
    if uploaded_file is not None:
        _handle_upload(uploaded_file)


def _render_document_list(docs: list[Path]) -> None:
    """Render the list of indexed documents (or an info hint when empty)."""
    st.subheader("📄 Documents")
    if not docs:
        st.info("No documents yet. Upload a PDF or Markdown file above.")
    else:
        for doc in docs:
            st.markdown(f"- {doc.name}")


def _render_stats(doc_count: int) -> None:
    """Render sidebar stats: document count and engine readiness."""
    st.subheader("📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Documents", doc_count)
    with col2:
        st.metric("Engine", "✅ Ready" if engine is not None else "❌ Offline")


def _render_sidebar() -> None:
    """Render the sidebar: branding, uploader, document list, stats."""
    with st.sidebar:
        _render_branding()
        st.divider()
        _render_uploader()
        st.divider()
        docs = _list_documents()
        _render_document_list(docs)
        st.divider()
        _render_stats(len(docs))


# ── Chat ────────────────────────────────────────────────────────────────────

def _render_header() -> None:
    """Render the branded header banner at the top of the chat area."""
    st.markdown(
        '<div class="rag-header">'
        "<h1>🔍 RAG Playground</h1>"
        "<p>Ask questions about your documents — "
        "powered by Retrieval-Augmented Generation</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_message_history() -> None:
    """Render prior chat messages, plus a welcome prompt when the chat is empty."""
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 Welcome! Upload documents in the sidebar, "
                "then ask me anything about them."
            )


def _append_message(role: str, content: str) -> None:
    """Record a chat message in session state and render it in the chat."""
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


def _generate_answer(prompt: str) -> str | None:
    """Query the engine and return the answer text.

    Returns ``None`` when the query fails; the error is rendered via
    ``st.error`` and recorded in the chat history so the user sees it.
    """
    try:
        response = engine.query(prompt)
        return response.response
    except Exception as exc:
        answer = f"❌ **Error:** {exc}"
        st.error(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        return None


def _render_chat() -> None:
    """Render the main chat area and handle the current user prompt."""
    _render_header()

    # Engine offline state
    if engine is None:
        st.error(
            "⚠️ **RAG engine is offline.**",
            icon="⚠️",
        )
        st.stop()

    _render_message_history()

    # Chat input
    prompt = st.chat_input("Ask a question about your documents…")
    if not prompt:
        return

    # ── User message ──
    _append_message("user", prompt)

    # ── Assistant response ──
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            answer = _generate_answer(prompt)
        if answer is not None:
            # Render inside the open assistant bubble, then record it in history.
            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point for the Streamlit app."""
    _inject_custom_css()
    _render_sidebar()
    _render_chat()


if __name__ == "__main__":
    main()
