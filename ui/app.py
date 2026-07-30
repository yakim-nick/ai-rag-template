"""RAG Playground — a Streamlit UI for the RAG service."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from rag import build_engine

# Module-level constant — can be reassigned for testing
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALLOWED_EXTENSIONS = {".md", ".pdf", ".txt", ".csv"}

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RAG Playground",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────

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

# ── Session state ───────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine_refresh" not in st.session_state:
    st.session_state.engine_refresh = 0


# ── Engine (cached, keyed by refresh counter) ───────────────────────────────

@st.cache_resource
def get_engine(_refresh: int) -> object | None:
    """Build the RAG query engine.  Returns ``None`` on failure."""
    try:
        return build_engine(str(DATA_DIR))
    except Exception:
        return None


engine = get_engine(st.session_state.engine_refresh)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _list_documents() -> list[Path]:
    """Return non-hidden files from the data directory."""
    if not DATA_DIR.exists():
        return []
    return sorted(
        f for f in DATA_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )


def _render_sidebar() -> None:
    """Render the sidebar: branding, uploader, document list, stats."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            "<h2>🔍 RAG Playground</h2>"
            "<p>Retrieval-Augmented Generation</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        # ── File upload ──
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["pdf", "md", "txt", "csv"],
            accept_multiple_files=False,
        )
        if uploaded_file is not None:
            _handle_upload(uploaded_file)

        st.divider()

        # ── Document list ──
        st.subheader("📄 Documents")
        docs = _list_documents()
        if not docs:
            st.info("No documents yet. Upload a PDF or Markdown file above.")
        else:
            for doc in docs:
                st.markdown(f"- {doc.name}")

        st.divider()

        # ── Stats ──
        st.subheader("📊 Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", len(docs))
        with col2:
            st.metric("Engine", "✅ Ready" if engine is not None else "❌ Offline")


def _handle_upload(uploaded_file) -> None:
    """Save an uploaded file to the data directory and trigger a rebuild."""
    file_path = DATA_DIR / uploaded_file.name
    try:
        file_bytes = uploaded_file.getvalue()
        file_path.write_bytes(file_bytes)
        st.toast(f"Uploaded **{uploaded_file.name}**", icon="✅")
        st.session_state.engine_refresh += 1
        st.rerun()
    except Exception as exc:
        st.error(f"Failed to save file: {exc}")


def _render_chat() -> None:
    """Render the main chat area."""
    st.markdown(
        '<div class="rag-header">'
        "<h1>🔍 RAG Playground</h1>"
        "<p>Ask questions about your documents — "
        "powered by Retrieval-Augmented Generation</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Engine offline state
    if engine is None:
        st.error(
            "⚠️ **RAG engine is offline.**",
            icon="⚠️",
        )
        st.stop()

    # Render message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Welcome prompt when chat is empty
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 Welcome! Upload documents in the sidebar, "
                "then ask me anything about them."
            )

    # Chat input
    prompt = st.chat_input("Ask a question about your documents…")
    if not prompt:
        return

    # ── User message ──
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ── Assistant response ──
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                response = engine.query(prompt)
                answer = response.response
            except Exception as exc:
                answer = f"❌ **Error:** {exc}"
                st.error(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
                return

        st.markdown(answer)
        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point for the Streamlit app."""
    _render_sidebar()
    _render_chat()


if __name__ == "__main__":
    main()
