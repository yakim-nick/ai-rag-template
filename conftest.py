"""Pytest bootstrap: make the repo root importable.

Tests import top-level modules (``app``, ``rag``, ``ui``) directly, so the
project root must be on ``sys.path`` regardless of how pytest is invoked.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
