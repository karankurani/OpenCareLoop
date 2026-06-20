#!/usr/bin/env python3
"""Import manually reviewed medication-image sidecars into SQLite.

This importer is intentionally small. The JSON sidecar remains the source of
truth. SQLite stores one row per sidecar plus a few summary columns that make
search and review easier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_STATUS = {"ok", "needs_review", "needs_user_review", "no_readable_content"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_spaces(text: str) -> str:
    return " ".join(str(text).split())


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_list(raw: object) -> list[object]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return [raw]


def clean_text_list(raw: object) -> list[str]:
    return [normalize_spaces(item) for item in clean_list(raw) if normalize_spaces(item)]


def read_source_files(raw: object, warnings: list[str]) -> tuple[list[dict[str, object]], str]:
    if not isinstance(raw, list):
        warnings.append("source_files must be a list")
        return [], ""

    source_files: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        if isinstance(item, str):
            item = {"path": item}
        if not isinstance(item, dict):
            warnings.append(f"source_files[{index}] is not an object or string")
            continue

        path_text = normalize_spaces(item.get("path") or item.get("source_file") or item.get("file") or "")
        if not path_text:
            warnings.append(f"source_files[{index}] is missing path")
            continue

        path = Path(path_text).expanduser()
        resolved_path = str(path.resolve()) if path.exists() else path_text
        recorded_hash = normalize_spaces(item.get("sha256") or item.get("source_sha256") or "")
        actual_hash = recorded_hash
        if path.exists():
            actual_hash = sha256_file(path)
            if recorded_hash and recorded_hash != actual_hash:
                warnings.append(f"source_files[{index}] sha256 does not match current file")
        elif not recorded_hash:
            warnings.append(f"source_files[{index}] source file not found and sha256 is missing")

        source_files.append(
            {
                "path": resolved_path,
                "sha256": actual_hash,
                "original_name": normalize_spaces(item.get("original_name") or path.name),
                "file_type": normalize_spaces(item.get("file_type") or ""),
                "page_order": item.get("page_order"),
                "notes": normalize_spaces(item.get("notes") or ""),
            }
        )

    manifest_basis = [
        {"path": item["path"], "sha256": item["sha256"], "page_order": item["page_order"]}
        for item in source_files
    ]
    manifest_hash = sha256_text(json_text(manifest_basis)) if manifest_basis else ""
    return source_files, manifest_hash


def iter_sidecar_files(paths: list[Path], recursive: bool):
    for path in paths:
        if path.is_file() and path.name.endswith(".medication-image.json"):
            yield path
        elif path.is_dir():
            pattern = "**/*.medication-image.json" if recursive else "*.medication-image.json"
            yield from sorted(path.glob(pattern))


def infer_db_path(inputs: list[Path]) -> Path:
    for raw_path in inputs:
        resolved = raw_path.expanduser().resolve(strict=False)
        candidate = resolved if resolved.name == "sidecars" else next(
            (parent for parent in (resolved, *resolved.parents) if parent.name == "sidecars"),
            None,
        )
        if candidate and candidate.parent.name == "medication-images":
            return candidate.parent / "medication_images.sqlite"
    raise ValueError(
        "Could not infer a medication-images SQLite path from the input paths. "
        "Use people/<person-slug>/medication-images/sidecars or pass --db explicitly."
    )


def infer_person_slug(path: Path) -> str:
    parts = path.resolve(strict=False).parts
    for index, part in enumerate(parts):
        if part == "people" and index + 1 < len(parts):
            return normalize_spaces(parts[index + 1])
    return ""


def summarize_medications(items: object) -> dict[str, object]:
    if not isinstance(items, list):
        items = []

    normalized_names: list[str] = []
    variants: list[str] = []
    compositions: list[str] = []
    raw_names: list[str] = []
    needs_name_confirmation = 0
    needs_schedule_confirmation = 0

    for item in items:
        if not isinstance(item, dict):
            continue
        raw_names.append(normalize_spaces(item.get("raw_name") or item.get("name") or ""))
        normalized_names.append(normalize_spaces(item.get("normalized_name") or ""))
        variants.append(normalize_spaces(item.get("variant") or ""))
        compositions.append(normalize_spaces(item.get("composition") or ""))
        if item.get("needs_name_confirmation"):
            needs_name_confirmation += 1
        if item.get("needs_schedule_confirmation"):
            needs_schedule_confirmation += 1

    def uniq(values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
        return ordered

    return {
        "raw_names": uniq(raw_names),
        "normalized_names": uniq(normalized_names),
        "variants": uniq(variants),
        "compositions": uniq(compositions),
        "needs_name_confirmation_count": needs_name_confirmation,
        "needs_schedule_confirmation_count": needs_schedule_confirmation,
    }


def load_sidecar(path: Path) -> dict[str, object]:
    sidecar = json.loads(path.read_text())
    if not isinstance(sidecar, dict):
        raise ValueError("sidecar root must be a JSON object")

    warnings = clean_text_list(sidecar.get("warnings"))
    capture_id = normalize_spaces(sidecar.get("capture_id") or "")
    if not capture_id:
        capture_id = path.name.removesuffix(".medication-image.json")
        warnings.append("capture_id was missing; derived from sidecar filename")

    person_slug = normalize_spaces(sidecar.get("person_slug") or "") or infer_person_slug(path)
    if not person_slug:
        warnings.append("person_slug was missing and could not be inferred from sidecar path")

    source_files, computed_manifest = read_source_files(sidecar.get("source_files", []), warnings)
    recorded_manifest = normalize_spaces(sidecar.get("source_manifest_sha256") or "")
    source_manifest_sha256 = recorded_manifest or computed_manifest
    if recorded_manifest and computed_manifest and recorded_manifest != computed_manifest:
        warnings.append("source_manifest_sha256 does not match source_files")

    unresolved_questions = clean_list(sidecar.get("unresolved_questions"))
    user_confirmations = clean_list(sidecar.get("user_confirmations"))
    medication_summary = summarize_medications(sidecar.get("identified_medications"))

    status = normalize_spaces(sidecar.get("status") or "ok").lower()
    if status not in ALLOWED_STATUS:
        warnings.append(f"invalid status {status!r}; kept as needs_review")
        status = "needs_review"
    if unresolved_questions and status == "ok":
        status = "needs_user_review"
    if (
        status == "ok"
        and (
            medication_summary["needs_name_confirmation_count"]
            or medication_summary["needs_schedule_confirmation_count"]
        )
    ):
        status = "needs_user_review"
    elif status == "ok" and warnings:
        status = "needs_review"

    return {
        "capture_id": capture_id,
        "person_slug": person_slug,
        "source_manifest_sha256": source_manifest_sha256,
        "sidecar_path": str(path.resolve()),
        "capture_date": sidecar.get("capture_date") or None,
        "capture_date_text": normalize_spaces(sidecar.get("capture_date_text") or ""),
        "ingested_at": sidecar.get("ingested_at") or utc_now(),
        "last_reprocessed_at": normalize_spaces(sidecar.get("last_reprocessed_at") or ""),
        "reprocess_reason": normalize_spaces(sidecar.get("reprocess_reason") or ""),
        "parser_version": normalize_spaces(sidecar.get("parser_version") or "manual-ai"),
        "status": status,
        "warnings": warnings,
        "unresolved_questions": unresolved_questions,
        "user_confirmations": user_confirmations,
        "source_files": source_files,
        "identified_medications": sidecar.get("identified_medications") if isinstance(sidecar.get("identified_medications"), list) else [],
        "pages": sidecar.get("pages") if isinstance(sidecar.get("pages"), list) else [],
        "sidecar_json": sidecar,
        **medication_summary,
    }


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma busy_timeout = 5000")
    conn.execute("pragma synchronous = normal")
    conn.execute(
        """
        create table if not exists medication_image_captures (
            id integer primary key,
            capture_id text not null unique,
            person_slug text not null,
            source_manifest_sha256 text not null,
            sidecar_path text not null,
            capture_date text,
            capture_date_text text,
            ingested_at text not null,
            last_reprocessed_at text,
            reprocess_reason text,
            parser_version text not null,
            status text not null,
            raw_names_json text not null,
            normalized_names_json text not null,
            variants_json text not null,
            compositions_json text not null,
            needs_name_confirmation_count integer not null,
            needs_schedule_confirmation_count integer not null,
            warnings_json text not null,
            unresolved_questions_json text not null,
            user_confirmations_json text not null,
            source_files_json text not null,
            pages_json text not null,
            identified_medications_json text not null,
            sidecar_json text not null,
            imported_at text not null
        )
        """
    )
    conn.execute("create index if not exists idx_mic_date on medication_image_captures(capture_date)")
    conn.execute("create index if not exists idx_mic_status on medication_image_captures(status)")


def write_db(db_path: Path, capture: dict[str, object]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    imported_at = utc_now()
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        init_db(conn)
        conn.execute(
            """
            insert into medication_image_captures (
                capture_id, person_slug, source_manifest_sha256, sidecar_path,
                capture_date, capture_date_text, ingested_at, last_reprocessed_at,
                reprocess_reason, parser_version, status, raw_names_json,
                normalized_names_json, variants_json, compositions_json,
                needs_name_confirmation_count, needs_schedule_confirmation_count,
                warnings_json, unresolved_questions_json, user_confirmations_json,
                source_files_json, pages_json, identified_medications_json,
                sidecar_json, imported_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(capture_id) do update set
                person_slug = excluded.person_slug,
                source_manifest_sha256 = excluded.source_manifest_sha256,
                sidecar_path = excluded.sidecar_path,
                capture_date = excluded.capture_date,
                capture_date_text = excluded.capture_date_text,
                ingested_at = excluded.ingested_at,
                last_reprocessed_at = excluded.last_reprocessed_at,
                reprocess_reason = excluded.reprocess_reason,
                parser_version = excluded.parser_version,
                status = excluded.status,
                raw_names_json = excluded.raw_names_json,
                normalized_names_json = excluded.normalized_names_json,
                variants_json = excluded.variants_json,
                compositions_json = excluded.compositions_json,
                needs_name_confirmation_count = excluded.needs_name_confirmation_count,
                needs_schedule_confirmation_count = excluded.needs_schedule_confirmation_count,
                warnings_json = excluded.warnings_json,
                unresolved_questions_json = excluded.unresolved_questions_json,
                user_confirmations_json = excluded.user_confirmations_json,
                source_files_json = excluded.source_files_json,
                pages_json = excluded.pages_json,
                identified_medications_json = excluded.identified_medications_json,
                sidecar_json = excluded.sidecar_json,
                imported_at = excluded.imported_at
            """,
            (
                capture["capture_id"],
                capture["person_slug"],
                capture["source_manifest_sha256"],
                capture["sidecar_path"],
                capture["capture_date"],
                capture["capture_date_text"],
                capture["ingested_at"],
                capture["last_reprocessed_at"],
                capture["reprocess_reason"],
                capture["parser_version"],
                capture["status"],
                json_text(capture["raw_names"]),
                json_text(capture["normalized_names"]),
                json_text(capture["variants"]),
                json_text(capture["compositions"]),
                capture["needs_name_confirmation_count"],
                capture["needs_schedule_confirmation_count"],
                json_text(capture["warnings"]),
                json_text(capture["unresolved_questions"]),
                json_text(capture["user_confirmations"]),
                json_text(capture["source_files"]),
                json_text(capture["pages"]),
                json_text(capture["identified_medications"]),
                json_text(capture["sidecar_json"]),
                imported_at,
            ),
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help=".medication-image.json files or directories")
    parser.add_argument("--db", type=Path, help="SQLite database path")
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
        print("No .medication-image.json sidecars found", file=sys.stderr)
        return 1

    imported = 0
    had_error = False
    for sidecar_path in sidecar_files:
        try:
            capture = load_sidecar(sidecar_path)
            write_db(args.db, capture)
        except Exception as exc:
            had_error = True
            print(f"ERROR {sidecar_path}: {exc}", file=sys.stderr)
            continue
        imported += 1
        print(
            f"{sidecar_path}: imported capture={capture['capture_id']}, "
            f"medications={len(capture['identified_medications'])}, "
            f"name confirmation={capture['needs_name_confirmation_count']}, "
            f"schedule confirmation={capture['needs_schedule_confirmation_count']}, "
            f"status={capture['status']}"
        )

    print(f"Imported {imported} sidecar(s) into {args.db}")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
