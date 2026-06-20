#!/usr/bin/env python3
"""Import manually reviewed imaging sidecars into SQLite.

This script deliberately does not parse imaging reports, procedure notes,
images, PDFs, OCR text, or handwritten annotations. The AI agent must inspect
each source and write the .imaging.json sidecar first.
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


ALLOWED_FINDING_TYPES = {
    "indication",
    "technique",
    "finding",
    "impression",
    "measurement",
    "procedure_detail",
    "injected_medication",
    "recommendation",
    "comparison",
    "note",
    "other",
}
ALLOWED_LATERALITY = {"left", "right", "bilateral", "midline", "not_applicable", "unknown"}
ALLOWED_MODALITY = {"ultrasound", "xray", "mri", "ct", "procedure", "unknown"}
ALLOWED_READABILITY = {"clear", "partial", "poor", "unreadable", ""}
ALLOWED_STATUS = {"ok", "needs_review", "needs_user_review", "no_readable_content"}
ALLOWED_STUDY_TYPES = {"diagnostic", "procedure", "mixed", "unknown"}


@dataclass
class PageReview:
    page: int | None
    source_file: str
    source_page: int | None
    readability: str
    notes: str
    warnings: list[str]


@dataclass
class ImagingFinding:
    finding_index: int
    finding_type: str
    label: str
    value_text: str
    normalized_value: str
    confidence: float
    needs_review: bool
    source_page: int | None
    source_file: str
    raw_visual_note: str
    warnings: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def duplicate_source_warnings(
    conn: sqlite3.Connection,
    table_name: str,
    id_column: str,
    current_id: str,
    source_manifest_sha256: str,
    source_files: list[dict],
) -> list[str]:
    warnings: list[str] = []
    current_hashes = {
        normalize_spaces(str(item.get("sha256") or "")): normalize_spaces(str(item.get("path") or ""))
        for item in source_files
        if normalize_spaces(str(item.get("sha256") or ""))
    }
    if not current_hashes and not source_manifest_sha256:
        return warnings

    rows = conn.execute(
        f"select {id_column}, source_manifest_sha256, source_files_json from {table_name} where {id_column} != ?",
        (current_id,),
    ).fetchall()
    for row_id, manifest_hash, source_files_json in rows:
        other_sources = []
        if source_files_json:
            try:
                raw_sources = json.loads(source_files_json)
                if isinstance(raw_sources, list):
                    other_sources = [item for item in raw_sources if isinstance(item, dict)]
            except json.JSONDecodeError:
                other_sources = []

        if source_manifest_sha256 and manifest_hash == source_manifest_sha256:
            warnings.append(
                f"duplicate source_manifest_sha256 matches existing {row_id}; likely the same multi-file study"
            )

        for other in other_sources:
            other_hash = normalize_spaces(str(other.get("sha256") or ""))
            if other_hash and other_hash in current_hashes:
                other_path = normalize_spaces(str(other.get("path") or ""))
                warnings.append(
                    f"duplicate source sha256 matches existing {row_id}: {other_path or other_hash}"
                )
    return sorted(set(warnings))


def clean_list(raw: object) -> list[object]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return [raw]


def clean_warnings(raw: object) -> list[str]:
    return [normalize_spaces(str(item)) for item in clean_list(raw) if normalize_spaces(str(item))]


def read_number(raw: object, field: str, warnings: list[str]) -> float:
    if raw is None or raw == "":
        return 0.0
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        warnings.append(f"{field} must be numeric; kept as 0")
        return 0.0
    return float(raw)


def read_int(raw: object, field: str, warnings: list[str]) -> int | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool) or not isinstance(raw, int):
        warnings.append(f"{field} must be an integer or null; kept as null")
        return None
    return raw


def read_choice(raw: object, allowed: set[str], default: str, field: str, warnings: list[str]) -> str:
    value = normalize_spaces(str(raw or "")).lower()
    if not value:
        return default
    if value not in allowed:
        warnings.append(f"{field} has invalid value {value!r}; kept as {default!r}")
        return default
    return value


def source_file_from_dict(raw: object, index: int, warnings: list[str]) -> dict:
    if isinstance(raw, str):
        data: dict[str, object] = {"path": raw}
    elif isinstance(raw, dict):
        data = dict(raw)
    else:
        warnings.append(f"source_files[{index}] is not an object or string; ignored")
        return {}

    source_path_text = normalize_spaces(str(data.get("path") or data.get("source_file") or data.get("file") or ""))
    if not source_path_text:
        warnings.append(f"source_files[{index}] is missing path")
        return {}

    source_path = Path(source_path_text).expanduser()
    resolved_path = str(source_path.resolve()) if source_path.exists() else source_path_text
    recorded_hash = normalize_spaces(str(data.get("sha256") or data.get("source_sha256") or ""))
    actual_hash = recorded_hash
    if source_path.exists():
        actual_hash = sha256_file(source_path)
        if recorded_hash and recorded_hash != actual_hash:
            warnings.append(f"source_files[{index}] sha256 does not match current file")
    elif not recorded_hash:
        warnings.append(f"source_files[{index}] source file not found and sha256 is missing")

    return {
        "path": resolved_path,
        "sha256": actual_hash,
        "original_name": normalize_spaces(str(data.get("original_name") or source_path.name)),
        "file_type": normalize_spaces(str(data.get("file_type") or "")),
        "page_order": read_int(data.get("page_order"), f"source_files[{index}].page_order", warnings),
        "notes": normalize_spaces(str(data.get("notes") or "")),
    }


def read_source_files(raw: object, warnings: list[str]) -> tuple[list[dict], str]:
    if not isinstance(raw, list):
        warnings.append("source_files must be a list")
        return [], ""

    source_files = []
    for index, item in enumerate(raw):
        source_file = source_file_from_dict(item, index, warnings)
        if source_file:
            source_files.append(source_file)

    manifest_basis = [
        {"path": item["path"], "sha256": item["sha256"], "page_order": item["page_order"]}
        for item in source_files
    ]
    manifest_hash = sha256_text(json_text(manifest_basis)) if manifest_basis else ""
    return source_files, manifest_hash


def page_from_dict(raw: object, index: int, warnings: list[str]) -> PageReview:
    row_warnings: list[str] = []
    if not isinstance(raw, dict):
        warnings.append(f"pages[{index}] is not an object; imported as review row")
        raw = {}

    readability = read_choice(
        raw.get("readability"),
        ALLOWED_READABILITY,
        "",
        f"pages[{index}].readability",
        row_warnings,
    )
    row_warnings.extend(clean_warnings(raw.get("warnings")))
    return PageReview(
        page=read_int(raw.get("page"), f"pages[{index}].page", row_warnings),
        source_file=normalize_spaces(str(raw.get("source_file") or "")),
        source_page=read_int(raw.get("source_page"), f"pages[{index}].source_page", row_warnings),
        readability=readability,
        notes=normalize_spaces(str(raw.get("notes") or "")),
        warnings=row_warnings,
    )


def finding_from_dict(raw: object, index: int, warnings: list[str]) -> ImagingFinding:
    row_warnings: list[str] = []
    if not isinstance(raw, dict):
        warnings.append(f"findings[{index}] is not an object; imported as review row")
        raw = {}

    finding_type = read_choice(
        raw.get("finding_type"),
        ALLOWED_FINDING_TYPES,
        "other",
        f"findings[{index}].finding_type",
        row_warnings,
    )
    value_text = normalize_spaces(str(raw.get("value_text") or ""))
    if not value_text:
        row_warnings.append(f"findings[{index}].value_text is missing")

    row_warnings.extend(clean_warnings(raw.get("warnings")))
    return ImagingFinding(
        finding_index=index,
        finding_type=finding_type,
        label=normalize_spaces(str(raw.get("label") or "")),
        value_text=value_text,
        normalized_value=normalize_spaces(str(raw.get("normalized_value") or "")),
        confidence=read_number(raw.get("confidence"), f"findings[{index}].confidence", row_warnings),
        needs_review=bool(raw.get("needs_review")) or bool(row_warnings),
        source_page=read_int(raw.get("source_page"), f"findings[{index}].source_page", row_warnings),
        source_file=normalize_spaces(str(raw.get("source_file") or "")),
        raw_visual_note=normalize_spaces(str(raw.get("raw_visual_note") or "")),
        warnings=row_warnings,
    )


def iter_sidecar_files(paths: list[Path], recursive: bool) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.name.endswith(".imaging.json"):
            yield path
        elif path.is_dir():
            pattern = "**/*.imaging.json" if recursive else "*.imaging.json"
            yield from sorted(path.glob(pattern))


def infer_db_path(inputs: list[Path]) -> Path:
    for raw_path in inputs:
        path = raw_path.expanduser()
        resolved = path.resolve(strict=False)
        candidate = resolved if resolved.name == "sidecars" else next(
            (parent for parent in (resolved, *resolved.parents) if parent.name == "sidecars"),
            None,
        )
        if candidate and candidate.parent.name == "imaging":
            return candidate.parent / "imaging.sqlite"
    raise ValueError(
        "Could not infer a person-scoped imaging SQLite path from the input paths. "
        "Use people/<person-slug>/imaging/sidecars or pass --db explicitly."
    )


def load_sidecar(path: Path) -> tuple[dict, list[PageReview], list[ImagingFinding]]:
    sidecar = json.loads(path.read_text())
    if not isinstance(sidecar, dict):
        raise ValueError("sidecar root must be a JSON object")

    warnings = clean_warnings(sidecar.get("warnings"))
    source_files, manifest_hash = read_source_files(sidecar.get("source_files"), warnings)
    if not source_files:
        warnings.append("no valid source_files were provided")

    raw_pages = sidecar.get("pages", [])
    if not isinstance(raw_pages, list):
        warnings.append("pages must be a list; imported with no page rows")
        raw_pages = []
    pages = [page_from_dict(item, idx, warnings) for idx, item in enumerate(raw_pages)]

    raw_findings = sidecar.get("findings", [])
    if not isinstance(raw_findings, list):
        warnings.append("findings must be a list; imported with no finding rows")
        raw_findings = []
    findings = [finding_from_dict(item, idx, warnings) for idx, item in enumerate(raw_findings)]

    study_id = normalize_spaces(str(sidecar.get("study_id") or ""))
    if not study_id:
        raise ValueError("study_id is required")

    unresolved_questions = [str(item) for item in clean_list(sidecar.get("unresolved_questions"))]
    status = read_choice(sidecar.get("status"), ALLOWED_STATUS, "ok", "status", warnings)
    needs_review_count = sum(1 for finding in findings if finding.needs_review)
    if status == "ok" and (warnings or unresolved_questions or needs_review_count):
        status = "needs_user_review" if unresolved_questions else "needs_review"

    return (
        {
            "study_id": study_id,
            "source_manifest_sha256": normalize_spaces(str(sidecar.get("source_manifest_sha256") or "")) or manifest_hash,
            "sidecar_path": str(path.resolve()),
            "patient_name": normalize_spaces(str(sidecar.get("patient_name") or "")),
            "study_date": sidecar.get("study_date") or None,
            "study_date_text": normalize_spaces(str(sidecar.get("study_date_text") or "")),
            "facility": normalize_spaces(str(sidecar.get("facility") or "")),
            "referring_doctor": normalize_spaces(str(sidecar.get("referring_doctor") or "")),
            "performing_doctor": normalize_spaces(str(sidecar.get("performing_doctor") or "")),
            "modality": read_choice(sidecar.get("modality"), ALLOWED_MODALITY, "unknown", "modality", warnings),
            "body_part": normalize_spaces(str(sidecar.get("body_part") or "")),
            "laterality": read_choice(sidecar.get("laterality"), ALLOWED_LATERALITY, "unknown", "laterality", warnings),
            "study_type": read_choice(sidecar.get("study_type"), ALLOWED_STUDY_TYPES, "unknown", "study_type", warnings),
            "ingested_at": sidecar.get("ingested_at") or utc_now(),
            "last_reprocessed_at": normalize_spaces(str(sidecar.get("last_reprocessed_at") or "")),
            "reprocess_reason": normalize_spaces(str(sidecar.get("reprocess_reason") or "")),
            "parser_version": sidecar.get("parser_version") or "manual-ai",
            "status": status,
            "warnings": warnings,
            "unresolved_questions": unresolved_questions,
            "user_confirmations": [str(item) for item in clean_list(sidecar.get("user_confirmations"))],
            "source_files": source_files,
            "finding_count": len(findings),
            "needs_review_count": needs_review_count,
        },
        pages,
        findings,
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma busy_timeout = 5000")
    conn.execute("pragma synchronous = normal")
    conn.execute("pragma foreign_keys = on")
    conn.execute(
        """
        create table if not exists imaging_studies (
            id integer primary key,
            study_id text not null unique,
            source_manifest_sha256 text not null,
            sidecar_path text not null,
            patient_name text,
            study_date text,
            study_date_text text,
            facility text,
            referring_doctor text,
            performing_doctor text,
            modality text not null,
            body_part text,
            laterality text not null,
            study_type text not null,
            ingested_at text not null,
            last_reprocessed_at text,
            reprocess_reason text,
            parser_version text not null,
            status text not null,
            warnings_json text not null,
            unresolved_questions_json text not null,
            user_confirmations_json text not null,
            source_files_json text not null,
            imported_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists imaging_pages (
            id integer primary key,
            study_id text not null references imaging_studies(study_id) on delete cascade,
            page integer,
            source_file text,
            source_page integer,
            readability text,
            notes text,
            warnings_json text not null,
            imported_at text not null
        )
        """
    )
    conn.execute(
        """
        create table if not exists imaging_findings (
            id integer primary key,
            study_id text not null references imaging_studies(study_id) on delete cascade,
            finding_index integer not null,
            finding_type text not null,
            label text,
            value_text text not null,
            normalized_value text,
            confidence real,
            needs_review integer not null,
            source_page integer,
            source_file text,
            raw_visual_note text,
            warnings_json text not null,
            imported_at text not null
        )
        """
    )
    conn.execute("create index if not exists idx_imaging_studies_date on imaging_studies(study_date)")
    conn.execute("create index if not exists idx_imaging_studies_body_part on imaging_studies(body_part)")
    conn.execute("create index if not exists idx_imaging_studies_status on imaging_studies(status)")
    conn.execute("create index if not exists idx_imaging_findings_type on imaging_findings(finding_type)")
    conn.execute("create index if not exists idx_imaging_findings_review on imaging_findings(needs_review)")


def write_db(
    db_path: Path,
    study: dict,
    pages: list[PageReview],
    findings: list[ImagingFinding],
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    imported_at = utc_now()
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        init_db(conn)
        study["warnings"] = sorted(
            set(
                list(study["warnings"])
                + duplicate_source_warnings(
                    conn,
                    "imaging_studies",
                    "study_id",
                    study["study_id"],
                    study["source_manifest_sha256"],
                    study["source_files"],
                )
            )
        )
        conn.execute(
            """
            insert into imaging_studies (
                study_id, source_manifest_sha256, sidecar_path, patient_name,
                study_date, study_date_text, facility, referring_doctor,
                performing_doctor, modality, body_part, laterality, study_type,
                ingested_at, last_reprocessed_at, reprocess_reason,
                parser_version, status, warnings_json, unresolved_questions_json,
                user_confirmations_json, source_files_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(study_id) do update set
                source_manifest_sha256 = excluded.source_manifest_sha256,
                sidecar_path = excluded.sidecar_path,
                patient_name = excluded.patient_name,
                study_date = excluded.study_date,
                study_date_text = excluded.study_date_text,
                facility = excluded.facility,
                referring_doctor = excluded.referring_doctor,
                performing_doctor = excluded.performing_doctor,
                modality = excluded.modality,
                body_part = excluded.body_part,
                laterality = excluded.laterality,
                study_type = excluded.study_type,
                ingested_at = excluded.ingested_at,
                last_reprocessed_at = excluded.last_reprocessed_at,
                reprocess_reason = excluded.reprocess_reason,
                parser_version = excluded.parser_version,
                status = excluded.status,
                warnings_json = excluded.warnings_json,
                unresolved_questions_json = excluded.unresolved_questions_json,
                user_confirmations_json = excluded.user_confirmations_json,
                source_files_json = excluded.source_files_json,
                imported_at = excluded.imported_at
            """,
            (
                study["study_id"],
                study["source_manifest_sha256"],
                study["sidecar_path"],
                study["patient_name"],
                study["study_date"],
                study["study_date_text"],
                study["facility"],
                study["referring_doctor"],
                study["performing_doctor"],
                study["modality"],
                study["body_part"],
                study["laterality"],
                study["study_type"],
                study["ingested_at"],
                study["last_reprocessed_at"],
                study["reprocess_reason"],
                study["parser_version"],
                study["status"],
                json_text(study["warnings"]),
                json_text(study["unresolved_questions"]),
                json_text(study["user_confirmations"]),
                json_text(study["source_files"]),
                imported_at,
            ),
        )
        conn.execute("delete from imaging_pages where study_id = ?", (study["study_id"],))
        conn.execute("delete from imaging_findings where study_id = ?", (study["study_id"],))
        conn.executemany(
            """
            insert into imaging_pages (
                study_id, page, source_file, source_page, readability,
                notes, warnings_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    study["study_id"],
                    page.page,
                    page.source_file,
                    page.source_page,
                    page.readability,
                    page.notes,
                    json_text(page.warnings),
                    imported_at,
                )
                for page in pages
            ],
        )
        conn.executemany(
            """
            insert into imaging_findings (
                study_id, finding_index, finding_type, label, value_text,
                normalized_value, confidence, needs_review, source_page,
                source_file, raw_visual_note, warnings_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    study["study_id"],
                    finding.finding_index,
                    finding.finding_type,
                    finding.label,
                    finding.value_text,
                    finding.normalized_value,
                    finding.confidence,
                    1 if finding.needs_review else 0,
                    finding.source_page,
                    finding.source_file,
                    finding.raw_visual_note,
                    json_text(finding.warnings),
                    imported_at,
                )
                for finding in findings
            ],
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help=".imaging.json files or directories")
    parser.add_argument(
        "--db",
        type=Path,
        help="SQLite database path; inferred from people/<person-slug>/imaging/sidecars when omitted",
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
        print("No .imaging.json sidecars found", file=sys.stderr)
        return 1

    imported = 0
    total_findings = 0
    total_review = 0
    had_error = False
    for sidecar_path in sidecar_files:
        try:
            study, pages, findings = load_sidecar(sidecar_path)
            write_db(args.db, study, pages, findings)
        except Exception as exc:
            had_error = True
            print(f"ERROR {sidecar_path}: {exc}", file=sys.stderr)
            continue
        imported += 1
        total_findings += len(findings)
        total_review += study["needs_review_count"]
        print(
            f"IMPORTED {sidecar_path} -> {args.db} "
            f"({len(findings)} findings, {study['needs_review_count']} need review, status={study['status']})"
        )

    print(
        f"Summary: imported={imported}, findings={total_findings}, needs_review={total_review}, "
        f"db={args.db}"
    )
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
