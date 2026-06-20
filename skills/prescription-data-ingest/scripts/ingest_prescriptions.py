#!/usr/bin/env python3
"""Import manually reviewed prescription sidecars into SQLite.

This script deliberately does not parse prescription images, PDFs, OCR text, or
medication instructions. The AI agent must inspect each source and write the
.prescription.json sidecar first.
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


ALLOWED_ACTIONS = {"start", "continue", "stop", "change", "unknown"}
ALLOWED_FACT_TYPES = {
    "diagnosis",
    "symptom",
    "vital",
    "test_advised",
    "lifestyle_advice",
    "follow_up",
    "referral",
    "note",
    "doctor_question",
    "other",
}
ALLOWED_READABILITY = {"clear", "partial", "poor", "unreadable", ""}
ALLOWED_STATUS = {"ok", "needs_review", "needs_user_review", "no_readable_content"}


@dataclass
class PageReview:
    page: int | None
    source_file: str
    source_page: int | None
    readability: str
    notes: str
    warnings: list[str]


@dataclass
class MedicationOrder:
    order_index: int
    raw_name: str
    normalized_name: str
    strength: str
    dose: str
    route: str
    frequency: str
    timing: str
    duration: str
    quantity: str
    action: str
    indication: str
    confidence: float
    needs_review: bool
    source_page: int | None
    source_file: str
    raw_visual_note: str
    warnings: list[str]


@dataclass
class ClinicalFact:
    fact_index: int
    fact_type: str
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
                f"duplicate source_manifest_sha256 matches existing {row_id}; likely the same multi-file encounter"
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

    page = read_int(raw.get("page"), f"pages[{index}].page", row_warnings)
    readability = normalize_spaces(str(raw.get("readability") or "")).lower()
    if readability not in ALLOWED_READABILITY:
        row_warnings.append(f"pages[{index}].readability is invalid; kept blank")
        readability = ""

    row_warnings.extend(clean_warnings(raw.get("warnings")))
    return PageReview(
        page=page,
        source_file=normalize_spaces(str(raw.get("source_file") or "")),
        source_page=read_int(raw.get("source_page"), f"pages[{index}].source_page", row_warnings),
        readability=readability,
        notes=normalize_spaces(str(raw.get("notes") or "")),
        warnings=row_warnings,
    )


def medication_from_dict(raw: object, index: int, warnings: list[str]) -> MedicationOrder:
    row_warnings: list[str] = []
    if not isinstance(raw, dict):
        warnings.append(f"medication_orders[{index}] is not an object; imported as review row")
        raw = {}

    raw_name = normalize_spaces(str(raw.get("raw_name") or raw.get("name") or ""))
    if not raw_name:
        row_warnings.append(f"medication_orders[{index}] is missing raw_name")

    action = normalize_spaces(str(raw.get("action") or "unknown")).lower()
    if action not in ALLOWED_ACTIONS:
        row_warnings.append(f"medication_orders[{index}].action is invalid; kept as unknown")
        action = "unknown"

    confidence = read_number(raw.get("confidence"), f"medication_orders[{index}].confidence", row_warnings)
    if confidence < 0 or confidence > 1:
        row_warnings.append(f"medication_orders[{index}].confidence must be between 0 and 1")
        confidence = max(0.0, min(1.0, confidence))

    row_warnings.extend(clean_warnings(raw.get("warnings")))
    source_page = read_int(raw.get("source_page"), f"medication_orders[{index}].source_page", row_warnings)
    return MedicationOrder(
        order_index=index,
        raw_name=raw_name,
        normalized_name=normalize_spaces(str(raw.get("normalized_name") or "")),
        strength=normalize_spaces(str(raw.get("strength") or "")),
        dose=normalize_spaces(str(raw.get("dose") or "")),
        route=normalize_spaces(str(raw.get("route") or "")),
        frequency=normalize_spaces(str(raw.get("frequency") or "")),
        timing=normalize_spaces(str(raw.get("timing") or "")),
        duration=normalize_spaces(str(raw.get("duration") or "")),
        quantity=normalize_spaces(str(raw.get("quantity") or "")),
        action=action,
        indication=normalize_spaces(str(raw.get("indication") or "")),
        confidence=confidence,
        needs_review=bool(raw.get("needs_review")) or bool(row_warnings),
        source_page=source_page,
        source_file=normalize_spaces(str(raw.get("source_file") or "")),
        raw_visual_note=normalize_spaces(str(raw.get("raw_visual_note") or raw.get("raw_line") or "")),
        warnings=row_warnings,
    )


def fact_from_dict(raw: object, index: int, warnings: list[str]) -> ClinicalFact:
    row_warnings: list[str] = []
    if not isinstance(raw, dict):
        warnings.append(f"clinical_facts[{index}] is not an object; imported as review row")
        raw = {}

    fact_type = normalize_spaces(str(raw.get("fact_type") or "other")).lower()
    if fact_type not in ALLOWED_FACT_TYPES:
        row_warnings.append(f"clinical_facts[{index}].fact_type is invalid; kept as other")
        fact_type = "other"

    value_text = normalize_spaces(str(raw.get("value_text") or raw.get("value") or ""))
    if not value_text:
        row_warnings.append(f"clinical_facts[{index}] is missing value_text")

    confidence = read_number(raw.get("confidence"), f"clinical_facts[{index}].confidence", row_warnings)
    if confidence < 0 or confidence > 1:
        row_warnings.append(f"clinical_facts[{index}].confidence must be between 0 and 1")
        confidence = max(0.0, min(1.0, confidence))

    row_warnings.extend(clean_warnings(raw.get("warnings")))
    source_page = read_int(raw.get("source_page"), f"clinical_facts[{index}].source_page", row_warnings)
    return ClinicalFact(
        fact_index=index,
        fact_type=fact_type,
        label=normalize_spaces(str(raw.get("label") or "")),
        value_text=value_text,
        normalized_value=normalize_spaces(str(raw.get("normalized_value") or "")),
        confidence=confidence,
        needs_review=bool(raw.get("needs_review")) or bool(row_warnings),
        source_page=source_page,
        source_file=normalize_spaces(str(raw.get("source_file") or "")),
        raw_visual_note=normalize_spaces(str(raw.get("raw_visual_note") or raw.get("raw_line") or "")),
        warnings=row_warnings,
    )


def iter_sidecar_files(paths: list[Path], recursive: bool) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.name.endswith(".prescription.json"):
            yield path
        elif path.is_dir():
            pattern = "**/*.prescription.json" if recursive else "*.prescription.json"
            yield from sorted(path.glob(pattern))


def infer_db_path(inputs: list[Path]) -> Path:
    for raw_path in inputs:
        path = raw_path.expanduser()
        resolved = path.resolve(strict=False)
        candidate = resolved if resolved.name == "sidecars" else next(
            (parent for parent in (resolved, *resolved.parents) if parent.name == "sidecars"),
            None,
        )
        if candidate and candidate.parent.name == "prescriptions":
            return candidate.parent / "prescriptions.sqlite"
    raise ValueError(
        "Could not infer a person-scoped prescriptions SQLite path from the input paths. "
        "Use people/<person-slug>/prescriptions/sidecars or pass --db explicitly."
    )


def load_sidecar(path: Path) -> tuple[dict, list[PageReview], list[MedicationOrder], list[ClinicalFact]]:
    sidecar = json.loads(path.read_text())
    if not isinstance(sidecar, dict):
        raise ValueError("sidecar root must be a JSON object")

    warnings = clean_warnings(sidecar.get("warnings"))
    encounter_id = normalize_spaces(str(sidecar.get("encounter_id") or ""))
    if not encounter_id:
        encounter_id = path.name.removesuffix(".prescription.json")
        warnings.append("encounter_id was missing; derived from sidecar filename")

    source_files, computed_manifest = read_source_files(sidecar.get("source_files", []), warnings)
    recorded_manifest = normalize_spaces(str(sidecar.get("source_manifest_sha256") or ""))
    source_manifest_sha256 = recorded_manifest or computed_manifest
    if recorded_manifest and computed_manifest and recorded_manifest != computed_manifest:
        warnings.append("source_manifest_sha256 does not match source_files")

    raw_pages = sidecar.get("pages", [])
    if not isinstance(raw_pages, list):
        warnings.append("pages must be a list; imported with no page rows")
        raw_pages = []
    pages = [page_from_dict(item, idx, warnings) for idx, item in enumerate(raw_pages)]

    raw_orders = sidecar.get("medication_orders", [])
    if not isinstance(raw_orders, list):
        warnings.append("medication_orders must be a list; imported with no medication rows")
        raw_orders = []
    medication_orders = [medication_from_dict(item, idx, warnings) for idx, item in enumerate(raw_orders)]

    raw_facts = sidecar.get("clinical_facts", [])
    if not isinstance(raw_facts, list):
        warnings.append("clinical_facts must be a list; imported with no fact rows")
        raw_facts = []
    clinical_facts = [fact_from_dict(item, idx, warnings) for idx, item in enumerate(raw_facts)]

    unresolved_questions = clean_list(sidecar.get("unresolved_questions"))
    user_confirmations = clean_list(sidecar.get("user_confirmations"))

    status = normalize_spaces(str(sidecar.get("status") or "ok")).lower()
    if status not in ALLOWED_STATUS:
        warnings.append(f"invalid status {status!r}; kept as needs_review")
        status = "needs_review"
    if unresolved_questions and status == "ok":
        status = "needs_user_review"
    elif (
        status == "ok"
        and (warnings or any(item.needs_review for item in medication_orders) or any(item.needs_review for item in clinical_facts))
    ):
        status = "needs_review"

    return (
        {
            "encounter_id": encounter_id,
            "source_manifest_sha256": source_manifest_sha256,
            "sidecar_path": str(path.resolve()),
            "source_files": source_files,
            "patient_name": normalize_spaces(str(sidecar.get("patient_name") or "")),
            "prescription_date": sidecar.get("prescription_date") or None,
            "prescription_date_text": normalize_spaces(str(sidecar.get("prescription_date_text") or "")),
            "prescriber": normalize_spaces(str(sidecar.get("prescriber") or "")),
            "clinic": normalize_spaces(str(sidecar.get("clinic") or "")),
            "ingested_at": sidecar.get("ingested_at") or utc_now(),
            "last_reprocessed_at": normalize_spaces(str(sidecar.get("last_reprocessed_at") or "")),
            "reprocess_reason": normalize_spaces(str(sidecar.get("reprocess_reason") or "")),
            "parser_version": normalize_spaces(str(sidecar.get("parser_version") or "manual-ai")),
            "status": status,
            "warnings": warnings,
            "unresolved_questions": unresolved_questions,
            "user_confirmations": user_confirmations,
        },
        pages,
        medication_orders,
        clinical_facts,
    )


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma busy_timeout = 5000")
    conn.execute("pragma synchronous = normal")
    conn.execute("pragma foreign_keys = on")
    conn.execute(
        """
        create table if not exists prescription_encounters (
            id integer primary key,
            encounter_id text not null unique,
            source_manifest_sha256 text not null,
            sidecar_path text not null,
            patient_name text,
            prescription_date text,
            prescription_date_text text,
            prescriber text,
            clinic text,
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
        create table if not exists prescription_pages (
            id integer primary key,
            encounter_id text not null references prescription_encounters(encounter_id) on delete cascade,
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
        create table if not exists medication_orders (
            id integer primary key,
            encounter_id text not null references prescription_encounters(encounter_id) on delete cascade,
            order_index integer not null,
            raw_name text not null,
            normalized_name text,
            strength text,
            dose text,
            route text,
            frequency text,
            timing text,
            duration text,
            quantity text,
            action text not null,
            indication text,
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
    conn.execute(
        """
        create table if not exists prescription_facts (
            id integer primary key,
            encounter_id text not null references prescription_encounters(encounter_id) on delete cascade,
            fact_index integer not null,
            fact_type text not null,
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
    conn.execute("create index if not exists idx_prescription_encounters_date on prescription_encounters(prescription_date)")
    conn.execute("create index if not exists idx_prescription_encounters_status on prescription_encounters(status)")
    conn.execute("create index if not exists idx_medication_orders_name on medication_orders(normalized_name, raw_name)")
    conn.execute("create index if not exists idx_medication_orders_review on medication_orders(needs_review)")
    conn.execute("create index if not exists idx_prescription_facts_type on prescription_facts(fact_type)")


def write_db(
    db_path: Path,
    encounter: dict,
    pages: list[PageReview],
    medication_orders: list[MedicationOrder],
    clinical_facts: list[ClinicalFact],
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    imported_at = utc_now()
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        init_db(conn)
        encounter["warnings"] = sorted(
            set(
                list(encounter["warnings"])
                + duplicate_source_warnings(
                    conn,
                    "prescription_encounters",
                    "encounter_id",
                    encounter["encounter_id"],
                    encounter["source_manifest_sha256"],
                    encounter["source_files"],
                )
            )
        )
        conn.execute(
            """
            insert into prescription_encounters (
                encounter_id, source_manifest_sha256, sidecar_path, patient_name,
                prescription_date, prescription_date_text, prescriber, clinic,
                ingested_at, last_reprocessed_at, reprocess_reason, parser_version,
                status, warnings_json, unresolved_questions_json,
                user_confirmations_json, source_files_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(encounter_id) do update set
                source_manifest_sha256 = excluded.source_manifest_sha256,
                sidecar_path = excluded.sidecar_path,
                patient_name = excluded.patient_name,
                prescription_date = excluded.prescription_date,
                prescription_date_text = excluded.prescription_date_text,
                prescriber = excluded.prescriber,
                clinic = excluded.clinic,
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
                encounter["encounter_id"],
                encounter["source_manifest_sha256"],
                encounter["sidecar_path"],
                encounter["patient_name"],
                encounter["prescription_date"],
                encounter["prescription_date_text"],
                encounter["prescriber"],
                encounter["clinic"],
                encounter["ingested_at"],
                encounter["last_reprocessed_at"],
                encounter["reprocess_reason"],
                encounter["parser_version"],
                encounter["status"],
                json_text(encounter["warnings"]),
                json_text(encounter["unresolved_questions"]),
                json_text(encounter["user_confirmations"]),
                json_text(encounter["source_files"]),
                imported_at,
            ),
        )
        conn.execute("delete from prescription_pages where encounter_id = ?", (encounter["encounter_id"],))
        conn.execute("delete from medication_orders where encounter_id = ?", (encounter["encounter_id"],))
        conn.execute("delete from prescription_facts where encounter_id = ?", (encounter["encounter_id"],))
        conn.executemany(
            """
            insert into prescription_pages (
                encounter_id, page, source_file, source_page, readability,
                notes, warnings_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    encounter["encounter_id"],
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
            insert into medication_orders (
                encounter_id, order_index, raw_name, normalized_name, strength,
                dose, route, frequency, timing, duration, quantity, action,
                indication, confidence, needs_review, source_page, source_file,
                raw_visual_note, warnings_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    encounter["encounter_id"],
                    order.order_index,
                    order.raw_name,
                    order.normalized_name,
                    order.strength,
                    order.dose,
                    order.route,
                    order.frequency,
                    order.timing,
                    order.duration,
                    order.quantity,
                    order.action,
                    order.indication,
                    order.confidence,
                    1 if order.needs_review else 0,
                    order.source_page,
                    order.source_file,
                    order.raw_visual_note,
                    json_text(order.warnings),
                    imported_at,
                )
                for order in medication_orders
            ],
        )
        conn.executemany(
            """
            insert into prescription_facts (
                encounter_id, fact_index, fact_type, label, value_text,
                normalized_value, confidence, needs_review, source_page,
                source_file, raw_visual_note, warnings_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    encounter["encounter_id"],
                    fact.fact_index,
                    fact.fact_type,
                    fact.label,
                    fact.value_text,
                    fact.normalized_value,
                    fact.confidence,
                    1 if fact.needs_review else 0,
                    fact.source_page,
                    fact.source_file,
                    fact.raw_visual_note,
                    json_text(fact.warnings),
                    imported_at,
                )
                for fact in clinical_facts
            ],
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help=".prescription.json files or directories")
    parser.add_argument(
        "--db",
        type=Path,
        help="SQLite database path; inferred from people/<person-slug>/prescriptions/sidecars when omitted",
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
        print("No .prescription.json sidecars found", file=sys.stderr)
        return 1

    imported = 0
    total_orders = 0
    total_facts = 0
    total_review = 0
    had_error = False
    for sidecar_path in sidecar_files:
        try:
            encounter, pages, orders, facts = load_sidecar(sidecar_path)
            write_db(args.db, encounter, pages, orders, facts)
        except Exception as exc:
            had_error = True
            print(f"ERROR {sidecar_path}: {exc}", file=sys.stderr)
            continue
        imported += 1
        total_orders += len(orders)
        total_facts += len(facts)
        review_count = sum(1 for item in orders if item.needs_review) + sum(1 for item in facts if item.needs_review)
        total_review += review_count
        print(
            f"{sidecar_path}: imported encounter={encounter['encounter_id']}, "
            f"{len(orders)} medication order(s), {len(facts)} fact(s), "
            f"{review_count} row(s) need review, status={encounter['status']}"
        )

    print(
        f"Imported {imported} sidecar(s), {total_orders} medication order(s), "
        f"{total_facts} fact(s), {total_review} row(s) needing review"
    )
    print(f"SQLite DB: {args.db}")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
