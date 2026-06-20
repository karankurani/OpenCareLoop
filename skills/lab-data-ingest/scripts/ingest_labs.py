#!/usr/bin/env python3
"""Import manually reviewed lab sidecars into SQLite.

This script deliberately does not parse source reports. The AI agent must
inspect each report page and write the .labs.json sidecar first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ALLOWED_FLAGS = {"low", "normal", "high", "critical", "abnormal", "unknown"}


@dataclass
class LabResult:
    test_name: str
    normalized_test_name: str
    value_text: str
    value_numeric: float | None
    unit: str
    reference_range: str
    flag: str
    specimen: str
    category: str
    page: int | None
    line_number: int | None
    confidence: float
    needs_review: bool
    raw_line: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_test_name(name: str) -> str:
    lowered = name.lower()
    return normalize_spaces(re.sub(r"[^a-z0-9%]+", " ", lowered))


def read_number(raw: object, field: str, warnings: list[str]) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        warnings.append(f"{field} must be numeric or null; kept as null")
        return None
    return float(raw)


def read_int(raw: object, field: str, warnings: list[str]) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int):
        warnings.append(f"{field} must be an integer or null; kept as null")
        return None
    return raw


def result_from_dict(raw: object, index: int, warnings: list[str]) -> LabResult:
    if not isinstance(raw, dict):
        warnings.append(f"results[{index}] is not an object; imported as review row")
        raw = {}

    warning_count_before = len(warnings)
    test_name = normalize_spaces(str(raw.get("test_name") or ""))
    if not test_name:
        warnings.append(f"results[{index}] is missing test_name")

    value_text = normalize_spaces(str(raw.get("value_text") or ""))
    if not value_text:
        warnings.append(f"results[{index}] is missing value_text")

    normalized = normalize_spaces(str(raw.get("normalized_test_name") or ""))
    flag = normalize_spaces(str(raw.get("flag") or "unknown")).lower()
    if flag not in ALLOWED_FLAGS:
        warnings.append(f"results[{index}] has invalid flag {flag!r}; kept as unknown")
        flag = "unknown"

    value_numeric = read_number(raw.get("value_numeric"), f"results[{index}].value_numeric", warnings)
    page = read_int(raw.get("page"), f"results[{index}].page", warnings)
    line_number = read_int(raw.get("line_number"), f"results[{index}].line_number", warnings)
    confidence = read_number(raw.get("confidence"), f"results[{index}].confidence", warnings)
    row_had_warning = len(warnings) > warning_count_before

    return LabResult(
        test_name=test_name,
        normalized_test_name=normalized or normalize_test_name(test_name),
        value_text=value_text,
        value_numeric=value_numeric,
        unit=normalize_spaces(str(raw.get("unit") or "")),
        reference_range=normalize_spaces(str(raw.get("reference_range") or "")),
        flag=flag,
        specimen=normalize_spaces(str(raw.get("specimen") or "")),
        category=normalize_spaces(str(raw.get("category") or "")),
        page=page,
        line_number=line_number,
        confidence=confidence if confidence is not None else 0.0,
        needs_review=bool(raw.get("needs_review")) or row_had_warning,
        raw_line=normalize_spaces(str(raw.get("raw_line") or "")),
    )


def iter_sidecar_files(paths: list[Path], recursive: bool) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.name.endswith(".labs.json"):
            yield path
        elif path.is_dir():
            pattern = "**/*.labs.json" if recursive else "*.labs.json"
            yield from sorted(path.glob(pattern))


def infer_db_path(inputs: list[Path]) -> Path:
    for raw_path in inputs:
        path = raw_path.expanduser()
        resolved = path.resolve(strict=False)
        candidate = resolved if resolved.name == "sidecars" else next(
            (parent for parent in (resolved, *resolved.parents) if parent.name == "sidecars"),
            None,
        )
        if candidate and candidate.parent.name == "labs":
            return candidate.parent / "labs.sqlite"
    raise ValueError(
        "Could not infer a person-scoped labs SQLite path from the input paths. "
        "Use people/<person-slug>/labs/sidecars or pass --db explicitly."
    )


def load_sidecar(path: Path) -> tuple[dict, list[LabResult]]:
    sidecar = json.loads(path.read_text())
    if not isinstance(sidecar, dict):
        raise ValueError("sidecar root must be a JSON object")

    warnings = [str(item) for item in sidecar.get("warnings", [])]
    raw_results = sidecar.get("results", [])
    if not isinstance(raw_results, list):
        warnings.append("results must be a list; imported with no result rows")
        raw_results = []
    results = [result_from_dict(item, idx, warnings) for idx, item in enumerate(raw_results)]

    source_file = normalize_spaces(str(sidecar.get("source_file") or ""))
    if not source_file:
        raise ValueError("source_file is required")
    source_path = Path(source_file).expanduser()
    if source_path.exists():
        source_file = str(source_path.resolve())
        source_sha256 = sha256_file(source_path)
        recorded_hash = normalize_spaces(str(sidecar.get("source_sha256") or ""))
        if recorded_hash and recorded_hash != source_sha256:
            warnings.append("source_sha256 did not match the current source file")
    else:
        source_sha256 = normalize_spaces(str(sidecar.get("source_sha256") or ""))
        warnings.append("source_file was not found during import")

    needs_review_count = sum(1 for result in results if result.needs_review)
    status = normalize_spaces(str(sidecar.get("status") or "ok"))
    if warnings or needs_review_count:
        status = "needs_review"

    return (
        {
            "source_file": source_file,
            "source_sha256": source_sha256,
            "sidecar_path": str(path.resolve()),
            "patient_name": normalize_spaces(str(sidecar.get("patient_name") or "")),
            "report_date": sidecar.get("report_date") or None,
            "report_date_text": normalize_spaces(str(sidecar.get("report_date_text") or "")),
            "ingested_at": sidecar.get("ingested_at") or utc_now(),
            "parser_version": sidecar.get("parser_version") or "manual-ai",
            "status": status,
            "warnings": warnings,
            "result_count": len(results),
            "needs_review_count": needs_review_count,
        },
        results,
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma busy_timeout = 5000")
    conn.execute("pragma synchronous = normal")
    conn.execute("pragma foreign_keys = on")
    conn.execute(
        """
        create table if not exists reports (
            id integer primary key,
            source_path text not null unique,
            source_sha256 text not null,
            sidecar_path text not null,
            patient_name text,
            report_date text,
            report_date_text text,
            ingested_at text not null,
            parser_version text not null,
            status text not null,
            warnings_json text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists lab_results (
            id integer primary key,
            report_id integer not null references reports(id) on delete cascade,
            test_name text not null,
            normalized_test_name text not null,
            value_text text not null,
            value_numeric real,
            unit text,
            reference_range text,
            flag text,
            specimen text,
            category text,
            page integer,
            line_number integer,
            confidence real,
            needs_review integer not null,
            raw_line text,
            created_at text not null
        )
        """
    )
    conn.execute("create index if not exists idx_lab_results_test on lab_results(normalized_test_name)")
    conn.execute("create index if not exists idx_lab_results_category on lab_results(category)")
    conn.execute("create index if not exists idx_reports_date on reports(report_date)")


def write_db(db_path: Path, sidecar: dict, results: list[LabResult]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        init_db(conn)
        conn.execute(
            """
            insert into reports (
                source_path, source_sha256, sidecar_path, patient_name, report_date,
                report_date_text, ingested_at, parser_version, status, warnings_json
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(source_path) do update set
                source_sha256 = excluded.source_sha256,
                sidecar_path = excluded.sidecar_path,
                patient_name = excluded.patient_name,
                report_date = excluded.report_date,
                report_date_text = excluded.report_date_text,
                ingested_at = excluded.ingested_at,
                parser_version = excluded.parser_version,
                status = excluded.status,
                warnings_json = excluded.warnings_json
            """,
            (
                sidecar["source_file"],
                sidecar["source_sha256"],
                sidecar["sidecar_path"],
                sidecar["patient_name"],
                sidecar["report_date"],
                sidecar["report_date_text"],
                sidecar["ingested_at"],
                sidecar["parser_version"],
                sidecar["status"],
                json.dumps(sidecar["warnings"], ensure_ascii=True),
            ),
        )
        report_id = conn.execute(
            "select id from reports where source_path = ?", (sidecar["source_file"],)
        ).fetchone()[0]
        conn.execute("delete from lab_results where report_id = ?", (report_id,))
        conn.executemany(
            """
            insert into lab_results (
                report_id, test_name, normalized_test_name, value_text, value_numeric,
                unit, reference_range, flag, specimen, category, page, line_number,
                confidence, needs_review, raw_line, created_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    report_id,
                    result.test_name,
                    result.normalized_test_name,
                    result.value_text,
                    result.value_numeric,
                    result.unit,
                    result.reference_range,
                    result.flag,
                    result.specimen,
                    result.category,
                    result.page,
                    result.line_number,
                    result.confidence,
                    1 if result.needs_review else 0,
                    result.raw_line,
                    sidecar["ingested_at"],
                )
                for result in results
            ],
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help=".labs.json files or directories")
    parser.add_argument(
        "--db",
        type=Path,
        help="SQLite database path; inferred from people/<person-slug>/labs/sidecars when omitted",
    )
    parser.add_argument("--recursive", action="store_true", help="Recurse into input directories")
    args = parser.parse_args(argv)
    if args.db is None:
        try:
            args.db = infer_db_path(args.inputs)
        except ValueError as exc:
            parser.error(str(exc))
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    sidecar_files = list(iter_sidecar_files(args.inputs, args.recursive))
    if not sidecar_files:
        print("No .labs.json sidecars found", file=sys.stderr)
        return 1

    imported = 0
    total_results = 0
    total_review = 0
    had_error = False
    for sidecar_path in sidecar_files:
        try:
            sidecar, results = load_sidecar(sidecar_path)
            write_db(args.db, sidecar, results)
        except Exception as exc:
            had_error = True
            print(f"ERROR {sidecar_path}: {exc}", file=sys.stderr)
            continue
        imported += 1
        total_results += int(sidecar["result_count"])
        total_review += int(sidecar["needs_review_count"])
        print(
            f"{sidecar_path}: imported {sidecar['result_count']} results, "
            f"{sidecar['needs_review_count']} need review, status={sidecar['status']}"
        )

    print(f"Imported {imported} sidecar(s), {total_results} result(s), {total_review} needing review")
    print(f"SQLite DB: {args.db}")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
