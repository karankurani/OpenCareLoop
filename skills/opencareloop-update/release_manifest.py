"""Shared release manifest — single source of truth for the tooling surface.

Imported by build_release_zip.py (to build the zip) and by the update skill
(to know what to replace and what to protect). Edit here only.
"""

from __future__ import annotations

# Root-level files that ship in every release. VERSION is injected by the
# build script at zip time, so it is absent here but accepted by the updater.
ROOT_FILES: list[str] = [
    "README.md",
    "START_HERE.md",
    "AGENTS.md",
    "CLAUDE.md",
    "SETUP.md",
    "LICENSE",
    "requirements.txt",
]

# File extensions collected recursively from skills/.
SKILL_FILE_SUFFIXES: frozenset[str] = frozenset({".md", ".py", ".yaml", ".yml"})

# Extensions that must never enter a release zip (binaries, sensitive docs).
BLOCKED_SUFFIXES: frozenset[str] = frozenset({
    ".db",
    ".doc",
    ".docx",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".sqlite",
    ".tif",
    ".tiff",
    ".webp",
    ".xls",
    ".xlsx",
})

# Path components that must never be included in the zip or touched by the
# updater. Any relative path whose parts intersect this set is rejected.
FORBIDDEN_PARTS: frozenset[str] = frozenset({
    ".git",
    ".github",
    ".venv",
    "docs-site",
    "node_modules",
    "people",
    "raw-data-dump",
    "__pycache__",
})
