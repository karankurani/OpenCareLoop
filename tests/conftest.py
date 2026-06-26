"""Shared pytest configuration.

Ensures the repo root is importable so ``tests/_loader.py`` resolves, then
re-exports :func:`load_script` for convenience.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests._loader import load_script  # noqa: E402,F401  (re-exported for tests)
