"""Import skill/script modules by file path.

The ingest scripts live under ``skills/<name>/scripts/`` and are not packaged
as importable modules (no ``__init__.py``, run as standalone CLIs). Tests load
them by path so we can exercise their functions directly without copying code.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_script(relpath: str, name: str | None = None) -> ModuleType:
    """Load a project Python file as a module given its repo-relative path."""
    path = ROOT / relpath
    if not path.is_file():
        raise FileNotFoundError(f"No such script: {path}")
    module_name = name or path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader, f"Could not build import spec for {path}"
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses/typing resolve the module by name.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
