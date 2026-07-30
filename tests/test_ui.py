"""Tests for the Streamlit UI (ui/app.py).

All tests in this module mock ``streamlit`` and ``rag.build_engine`` so the
UI can be imported and exercised without a real Streamlit server or a real
embedding model.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest


# ── Mock helpers ────────────────────────────────────────────────────────────


class MockSessionState(dict):
    """A dict that also supports attribute access, like real ``st.session_state``."""

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value):
        self[name] = value


class _CM:
    """A context manager that also quacks like a Streamlit container."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @staticmethod
    def metric(*_, **__):
        pass

    @staticmethod
    def markdown(*_, **__):
        pass

    @staticmethod
    def error(*_, **__):
        pass


def _build_mock_streamlit() -> types.ModuleType:
    """Return a fake ``streamlit`` module suitable for testing ``ui.app``."""
    mock_st = types.ModuleType("streamlit")

    # Session state — supports both dict-like and attribute access
    mock_st.session_state = MockSessionState()

    # sidebar is a context manager object
    mock_st.sidebar = _CM()

    # chat_message — MagicMock that returns a context manager
    mock_st.chat_message = MagicMock(return_value=_CM())

    # spinner — MagicMock that returns a context manager
    mock_st.spinner = MagicMock(return_value=_CM())

    # empty — returns a context manager
    mock_st.empty = MagicMock(return_value=_CM())

    # columns — returns list of context managers
    def _columns(n):
        return [_CM() for _ in range(n)]

    mock_st.columns = _columns

    # cache_resource — identity decorator (no real caching)
    def _cache_resource(func=None, **kwargs):
        if func is not None:
            return func
        return lambda f: f

    mock_st.cache_resource = _cache_resource

    # Display stubs
    mock_st.set_page_config = MagicMock()
    mock_st.markdown = MagicMock()
    mock_st.title = MagicMock()
    mock_st.subheader = MagicMock()
    mock_st.caption = MagicMock()
    mock_st.divider = MagicMock()
    mock_st.metric = MagicMock()
    mock_st.error = MagicMock()
    mock_st.info = MagicMock()
    mock_st.success = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.toast = MagicMock()
    mock_st.stop = MagicMock()
    mock_st.rerun = MagicMock()

    # Input stubs (no-op by default)
    mock_st.file_uploader = MagicMock(return_value=None)
    mock_st.chat_input = MagicMock(return_value=None)
    mock_st.button = MagicMock(return_value=False)

    return mock_st


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock streamlit + mock rag, then import ``ui.app``.

    Because ``ui.app`` guards its ``main()`` behind ``if __name__ == "__main__"``,
    importing the module only runs module-level initialisation (page config,
    session state, engine build).  Tests can then tweak mocks / session state /
    ``DATA_DIR`` before calling ``app.main()`` explicitly.

    Yields ``(app, mock_st, mock_engine)``.
    """
    # Ensure a fresh import
    for mod in list(sys.modules):
        if mod == "ui" or mod.startswith("ui."):
            del sys.modules[mod]

    mock_st = _build_mock_streamlit()
    sys.modules["streamlit"] = mock_st

    # Mock the RAG engine
    mock_engine = MagicMock()
    mock_engine.query.return_value.response = "This is a test answer."
    monkeypatch.setattr("rag.build_engine", MagicMock(return_value=mock_engine))

    # Now import — only module-level code runs, NOT main()
    import ui.app as _app

    yield _app, mock_st, mock_engine

    # Teardown: remove cached module so next test starts clean
    for mod in list(sys.modules):
        if mod == "ui" or mod.startswith("ui."):
            del sys.modules[mod]


# ── Tests ───────────────────────────────────────────────────────────────────


def test_module_imports(mock_env):
    """Smoke test: the UI module can be imported without errors."""
    app, _, _ = mock_env
    assert hasattr(app, "DATA_DIR")
    assert hasattr(app, "main")
    assert callable(app.main)


def test_chat_flow_processes_question(mock_env):
    """A non-None ``chat_input`` triggers query and stores the response."""
    app, mock_st, mock_engine = mock_env
    mock_st.chat_input.return_value = "What is RAG?"

    app.main()

    # The engine should have been called with the user's question
    mock_engine.query.assert_called_once()
    args, _ = mock_engine.query.call_args
    assert args[0] == "What is RAG?"

    # The response should be in session state messages
    messages = mock_st.session_state.get("messages", [])
    assert len(messages) >= 2  # user + assistant

    # Last message should be the assistant's response
    last = messages[-1]
    assert last["role"] == "assistant"
    assert "test answer" in last["content"].lower()


def test_empty_chat_shows_welcome(mock_env):
    """With no messages yet and no input, the assistant shows a welcome."""
    app, mock_st, _ = mock_env
    mock_st.chat_input.return_value = None  # no question submitted

    app.main()

    # Should be no user/assistant messages
    messages = mock_st.session_state.get("messages", [])
    assert len(messages) == 0

    # Welcome message rendered — chat_message was called for assistant
    mock_st.chat_message.assert_any_call("assistant")


def test_engine_offline_shows_error(mock_env):
    """When ``build_engine`` returns None, the UI shows an error and stops."""
    app, mock_st, _ = mock_env

    # Simulate engine build failure by reassigning the module-level engine var
    # (The real build_engine was already mocked to return a valid engine during
    #  import, so we replace app.engine directly.)
    app.engine = None

    app.main()

    # Error should have been displayed
    mock_st.error.assert_called()
    # st.stop() should have been called to halt rendering
    mock_st.stop.assert_called_once()


def test_query_error_handled_gracefully(mock_env):
    """If ``engine.query`` raises, the error is shown in the chat."""
    app, mock_st, mock_engine = mock_env
    mock_st.chat_input.return_value = "Will this crash?"
    mock_engine.query.side_effect = ValueError("Something went wrong")

    app.main()

    # An error message should have been rendered
    mock_st.error.assert_called()

    # The error text should be stored in session state
    messages = mock_st.session_state.get("messages", [])
    assert any("error" in m.get("content", "").lower() for m in messages)


def test_file_upload_triggers_rebuild(mock_env, tmp_path):
    """Uploading a file saves it and increments the engine refresh counter."""
    app, mock_st, _ = mock_env

    # Override DATA_DIR to a temp directory
    original_data_dir = app.DATA_DIR
    app.DATA_DIR = tmp_path

    # Mock file upload
    mock_file = MagicMock()
    mock_file.name = "test_doc.md"
    mock_file.getvalue.return_value = b"# Test content"
    mock_st.file_uploader.return_value = mock_file

    app.main()

    try:
        # File should have been written to disk
        saved_file = tmp_path / "test_doc.md"
        assert saved_file.exists()
        assert saved_file.read_text() == "# Test content"

        # Engine refresh should have been incremented
        assert mock_st.session_state.get("engine_refresh", 0) == 1

        # rerun should have been called
        mock_st.rerun.assert_called_once()
    finally:
        app.DATA_DIR = original_data_dir


def test_document_list_shown_in_sidebar(mock_env, tmp_path):
    """The sidebar lists documents found in the data directory."""
    app, mock_st, _ = mock_env

    # Create test files
    (tmp_path / "doc1.md").write_text("# Doc 1")
    (tmp_path / "doc2.pdf").write_text("PDF content")
    (tmp_path / ".hidden").write_text("hidden")

    original_data_dir = app.DATA_DIR
    app.DATA_DIR = tmp_path

    app.main()

    try:
        # st.subheader should have been called with "📄 Documents"
        mock_st.subheader.assert_any_call("📄 Documents")

        # Collect document names from markdown calls that start with "- "
        markdown_calls = [
            c for c in mock_st.markdown.call_args_list
            if c.args and isinstance(c.args[0], str) and c.args[0].startswith("- ")
        ]
        doc_names = [c.args[0].removeprefix("- ") for c in markdown_calls]
        assert "doc1.md" in doc_names
        assert "doc2.pdf" in doc_names
        assert ".hidden" not in doc_names
    finally:
        app.DATA_DIR = original_data_dir


def test_no_documents_shows_info(mock_env, tmp_path):
    """With no documents in the data dir, an info message is shown."""
    app, mock_st, _ = mock_env

    original_data_dir = app.DATA_DIR
    app.DATA_DIR = tmp_path  # empty temp dir

    app.main()

    try:
        # info should have been called about no documents
        mock_st.info.assert_called()
    finally:
        app.DATA_DIR = original_data_dir
