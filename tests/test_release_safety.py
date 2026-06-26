"""Guard the release-packaging invariants.

These tests protect a privacy-critical promise: a release zip must never carry
``people/`` medical data, the ``.venv``, git internals, or binary/sensitive
file types. They pin the manifest and the path safety check that enforce it.
"""

from __future__ import annotations

import pytest

from tests._loader import ROOT, load_script

manifest = load_script(
    "skills/opencareloop-update/release_manifest.py", "release_manifest"
)
build = load_script("scripts/build_release_zip.py", "build_release_zip")


def test_people_and_venv_are_forbidden_parts():
    # The whole point of the workspace: dossier data never ships.
    assert "people" in manifest.FORBIDDEN_PARTS
    assert ".venv" in manifest.FORBIDDEN_PARTS
    assert ".git" in manifest.FORBIDDEN_PARTS
    assert "__pycache__" in manifest.FORBIDDEN_PARTS


def test_medical_binary_suffixes_are_blocked():
    for suffix in (".pdf", ".png", ".jpg", ".sqlite", ".xlsx", ".docx"):
        assert suffix in manifest.BLOCKED_SUFFIXES


def test_shipped_skill_suffixes_exclude_sqlite_and_pdf():
    assert manifest.SKILL_FILE_SUFFIXES.isdisjoint(manifest.BLOCKED_SUFFIXES)
    # Source/docs that should ship.
    assert {".py", ".md", ".yaml"} <= set(manifest.SKILL_FILE_SUFFIXES)


def test_assert_safe_path_rejects_people_dir():
    bad = ROOT / "people" / "jane" / "profile.md"
    with pytest.raises(SystemExit):
        build.assert_safe_path(bad)


def test_assert_safe_path_rejects_blocked_suffix():
    bad = ROOT / "skills" / "lab-data-ingest" / "references" / "scan.pdf"
    with pytest.raises(SystemExit):
        build.assert_safe_path(bad)


def test_assert_safe_path_allows_skill_source():
    ok = ROOT / "skills" / "lab-data-ingest" / "scripts" / "ingest_labs.py"
    build.assert_safe_path(ok)  # must not raise


def test_iter_release_files_excludes_people_and_includes_root_docs():
    files = build.iter_release_files()
    rels = {p.relative_to(ROOT).as_posix() for p in files}
    assert "AGENTS.md" in rels
    assert not any(r.startswith("people/") for r in rels)
    assert not any(r.endswith(".pdf") for r in rels)
