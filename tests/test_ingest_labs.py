"""Tests for the lab-data-ingest sidecar importer.

Exemplar suite: the other ``ingest_*.py`` scripts share this shape (pure
normalizers + a row dataclass builder + a SQLite writer), so mirror these
patterns when adding their suites.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from tests._loader import load_script

labs = load_script("skills/lab-data-ingest/scripts/ingest_labs.py", "ingest_labs")


# --- pure normalizers -------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  hello   world ", "hello world"),
        ("\tHbA1c\n\n", "HbA1c"),
        ("", ""),
    ],
)
def test_normalize_spaces(raw, expected):
    assert labs.normalize_spaces(raw) == expected


def test_normalize_test_name_strips_punctuation_and_lowercases():
    assert labs.normalize_test_name("Vitamin D (25-OH), serum") == "vitamin d 25 oh serum"
    # '%' is preserved because it is clinically meaningful.
    assert labs.normalize_test_name("HbA1c %") == "hba1c %"


def test_read_number_accepts_numeric_rejects_bool_and_str():
    warnings: list[str] = []
    assert labs.read_number(None, "f", warnings) is None
    assert labs.read_number(3, "f", warnings) == 3.0
    assert labs.read_number(2.5, "f", warnings) == 2.5
    assert warnings == []
    # bool is an int subclass but must not be treated as numeric.
    assert labs.read_number(True, "f", warnings) is None
    assert labs.read_number("12", "f", warnings) is None
    assert len(warnings) == 2


def test_read_int_rejects_float_and_bool():
    warnings: list[str] = []
    assert labs.read_int(None, "f", warnings) is None
    assert labs.read_int(4, "f", warnings) == 4
    assert labs.read_int(4.0, "f", warnings) is None
    assert labs.read_int(False, "f", warnings) is None
    assert len(warnings) == 2


# --- result_from_dict -------------------------------------------------------


def test_result_from_dict_valid_row_has_no_warnings():
    warnings: list[str] = []
    row = labs.result_from_dict(
        {
            "test_name": "Hemoglobin",
            "value_text": "13.5",
            "value_numeric": 13.5,
            "unit": "g/dL",
            "reference_range": "13.0-17.0",
            "flag": "Normal",
            "page": 1,
            "line_number": 7,
            "confidence": 0.9,
        },
        0,
        warnings,
    )
    assert warnings == []
    assert row.test_name == "Hemoglobin"
    assert row.normalized_test_name == "hemoglobin"
    assert row.flag == "normal"  # lowercased
    assert row.value_numeric == 13.5
    assert row.needs_review is False


def test_result_from_dict_invalid_flag_falls_back_to_unknown():
    warnings: list[str] = []
    row = labs.result_from_dict(
        {"test_name": "X", "value_text": "1", "flag": "sky-high"}, 0, warnings
    )
    assert row.flag == "unknown"
    assert row.needs_review is True  # any row warning forces review
    assert any("invalid flag" in w for w in warnings)


def test_result_from_dict_missing_fields_flag_review():
    warnings: list[str] = []
    row = labs.result_from_dict({}, 2, warnings)
    assert row.needs_review is True
    assert any("missing test_name" in w for w in warnings)
    assert any("missing value_text" in w for w in warnings)


def test_result_from_dict_non_dict_input_is_demoted_to_review_row():
    warnings: list[str] = []
    row = labs.result_from_dict("not-an-object", 5, warnings)
    assert row.needs_review is True
    assert any("not an object" in w for w in warnings)


def test_result_from_dict_explicit_needs_review_is_honored():
    warnings: list[str] = []
    row = labs.result_from_dict(
        {"test_name": "X", "value_text": "1", "needs_review": True}, 0, warnings
    )
    assert row.needs_review is True
    assert warnings == []  # no field problems, just an explicit flag


# --- infer_db_path ----------------------------------------------------------


def test_infer_db_path_from_sidecars_dir(tmp_path):
    sidecars = tmp_path / "people" / "jane" / "labs" / "sidecars"
    sidecars.mkdir(parents=True)
    assert labs.infer_db_path([sidecars]) == sidecars.parent / "labs.sqlite"


def test_infer_db_path_from_file_inside_sidecars(tmp_path):
    sidecars = tmp_path / "people" / "jane" / "labs" / "sidecars"
    sidecars.mkdir(parents=True)
    f = sidecars / "report.labs.json"
    f.write_text("{}")
    assert labs.infer_db_path([f]) == sidecars.parent / "labs.sqlite"


def test_infer_db_path_rejects_unscoped_path(tmp_path):
    with pytest.raises(ValueError):
        labs.infer_db_path([tmp_path / "random" / "dir"])


# --- load_sidecar -----------------------------------------------------------


def _write_sidecar(tmp_path, data: dict):
    path = tmp_path / "r.labs.json"
    path.write_text(json.dumps(data))
    return path


def test_load_sidecar_requires_source_file(tmp_path):
    path = _write_sidecar(tmp_path, {"results": []})
    with pytest.raises(ValueError, match="source_file is required"):
        labs.load_sidecar(path)


def test_load_sidecar_missing_source_file_warns_and_needs_review(tmp_path):
    path = _write_sidecar(
        tmp_path,
        {"source_file": "/nope/missing.pdf", "results": [], "status": "ok"},
    )
    sidecar, results = labs.load_sidecar(path)
    assert results == []
    assert sidecar["status"] == "needs_review"
    assert any("not found" in w for w in sidecar["warnings"])


def test_load_sidecar_non_list_results_warns(tmp_path):
    path = _write_sidecar(
        tmp_path, {"source_file": "/nope.pdf", "results": {"oops": 1}}
    )
    sidecar, results = labs.load_sidecar(path)
    assert results == []
    assert any("results must be a list" in w for w in sidecar["warnings"])


# --- write_db round trip ----------------------------------------------------


def test_write_db_round_trip_and_idempotent_upsert(tmp_path):
    src = tmp_path / "source.pdf"
    src.write_bytes(b"%PDF-fake")
    sidecar_path = _write_sidecar(
        tmp_path,
        {
            "source_file": str(src),
            "report_date": "2026-01-15",
            "results": [
                {"test_name": "Hemoglobin", "value_text": "13.5", "value_numeric": 13.5},
                {"test_name": "Glucose", "value_text": "90", "value_numeric": 90},
            ],
        },
    )
    db = tmp_path / "labs.sqlite"

    sidecar, results = labs.load_sidecar(sidecar_path)
    labs.write_db(db, sidecar, results)

    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from reports").fetchone()[0] == 1
        assert conn.execute("select count(*) from lab_results").fetchone()[0] == 2

    # Re-importing the same source must upsert, not duplicate.
    sidecar2, results2 = labs.load_sidecar(sidecar_path)
    labs.write_db(db, sidecar2, results2)
    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from reports").fetchone()[0] == 1
        assert conn.execute("select count(*) from lab_results").fetchone()[0] == 2
