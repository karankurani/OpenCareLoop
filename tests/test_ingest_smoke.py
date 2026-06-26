"""Cheap cross-skill guard: every ingest script must import and expose its CLI.

This catches syntax errors and broken refactors in the ingest scripts that do
not yet have a full suite like ``test_ingest_labs.py``. Extend those scripts
with dedicated suites over time; this keeps them from rotting in the meantime.
"""

from __future__ import annotations

import pytest

from tests._loader import load_script

INGEST_SCRIPTS = [
    "skills/lab-data-ingest/scripts/ingest_labs.py",
    "skills/imaging-data-ingest/scripts/ingest_imaging.py",
    "skills/medication-image-ingest/scripts/ingest_medication_images.py",
    "skills/prescription-data-ingest/scripts/ingest_prescriptions.py",
]


@pytest.mark.parametrize("relpath", INGEST_SCRIPTS)
def test_ingest_script_imports_and_has_entrypoints(relpath):
    module = load_script(relpath, relpath.replace("/", "_"))
    assert callable(module.main)
    assert callable(module.parse_args)
