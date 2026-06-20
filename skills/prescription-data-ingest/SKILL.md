---
name: prescription-data-ingest
description: Manually ingest a person's prescription photos, scans, PDFs, and handwritten doctor instructions into one JSON sidecar per prescription encounter and a searchable SQLite index. Use when Codex needs to classify prescription files from a person-local raw intake folder, group multi-image prescriptions, manually extract medication orders, vitals, tests advised, follow-up instructions, unresolved questions, or reprocess a previously ingested prescription without relying on automated medication parsing.
---

# Prescription Data Ingest

## Core Rule

Manually read the prescription yourself as the AI agent. Use image viewing, local OCR, PDF text extraction, zooming, rotation, or contrast checks only as support for readability. Do not use code, OCR, regexes, or parser heuristics to decide which medicines, doses, frequencies, durations, diagnoses, or instructions are present.

Treat prescriptions as qualitative clinical encounters. Capture uncertainty plainly and ask the user before finalizing any unclear medication name, dose, duration, date, action, indication, or current-vs-past status.

## Workflow

1. Start from `people/<person-slug>/raw-data-dump/` and classify files before extraction.
2. Work in small batches: one prescription encounter at a time, or a tightly
   related multi-page encounter when all pages clearly belong together.
3. Before creating a new encounter, compare each raw file against already
   ingested prescription/imaging records in two ways: first by source
   hashes/manifests when available, and then by manual content review of date,
   doctor, patient, medicine lines, instructions, page layout, handwriting, and
   whether the image is the front/back or a clearer recapture of an existing
   page. If the file belongs to an existing encounter, do not create a new
   encounter. Reprocess the existing encounter instead, or leave the duplicate
   in intake until the user says whether to discard it.
4. If encounter grouping, duplicate status, patient identity, date, or whether
   pages belong together is unclear, stop before moving/importing and ask the
   user a focused review question.
5. Group all images/pages from the same prescription encounter. Create one encounter sidecar even when the prescription has multiple JPGs/PDF pages.
6. Move grouped originals to `people/<person-slug>/prescriptions/raw/<encounter-id>/`. Preserve original filenames.
7. Manually inspect each source page/image in order. Record page-level readability issues, cropped areas, handwriting ambiguity, and any alternate local view used.
8. Cross-check readable or user-confirmed medicine names online to verify the
   likely product/generic name and composition. Record what was verified, what
   source context connects it to this prescription, and what remains uncertain
   in `normalized_name`, `indication`, `raw_visual_note`, `warnings`, or
   `clinical_facts` notes as appropriate. Do not use web results to override
   unclear handwriting, doses, frequencies, durations, or current-vs-past
   status.
9. Draft one JSON sidecar under `people/<person-slug>/prescriptions/sidecars/` with suffix `.prescription.json`.
10. If important details are unclear, keep them in `unresolved_questions`, set `status: "needs_user_review"`, ask the user in one focused batch, then incorporate answers into `user_confirmations`.
11. Set `status` to `ok` only when no important source or user-review issues remain. Use `needs_review` for non-user technical/readability uncertainty and `no_readable_content` only when the source cannot be read locally.
12. Validate the sidecar JSON mechanically, then import it into SQLite:

```bash
.venv/bin/python skills/prescription-data-ingest/scripts/ingest_prescriptions.py people/example-person/prescriptions/sidecars --recursive
```

13. Before updating dossier Markdown, use `skills/dossier-sync` and its confirmed-facts-only rules. Update `medications.md`, `timeline.md`, visit notes, `current-concerns.md`, or `questions-for-doctor.md` only when the relevant prescription facts are confirmed or explicitly need a marked open question.
14. After each batch, report the source files handled, encounter ID, sidecar
    path, SQLite import status, unresolved questions, and the next proposed
    prescription batch.

## Duplicate Handling

- Treat exact duplicate files as the same source when `sha256` matches an
  existing ingested source file.
- Treat exact duplicate multi-file encounters as the same encounter when the
  ordered `source_manifest_sha256` matches an existing ingested encounter.
- Also treat non-identical photos as the same source when manual review shows
  they are the same prescription page, the back side of an already ingested
  page, or a clearer/recropped version of an existing image.
- If a new image is not byte-identical but is clearly a clearer photo of the
  same prescription page or same encounter, reprocess the existing encounter
  instead of creating a second encounter for the same event.
- Keep duplicate warnings in the sidecar/import output so future agents can see
  why a record was merged or held for review.

## Reprocessing

Reprocess an encounter when the user supplies missing details, a better image arrives, a prior read looks wrong, or medication history needs correction.

- Re-read the original files from `people/<person-slug>/prescriptions/raw/<encounter-id>/`.
- Overwrite the current sidecar for that encounter; do not create archived sidecar revisions by default.
- Preserve `encounter_id`, update `last_reprocessed_at`, and write a short `reprocess_reason`.
- Add user-provided corrections to `user_confirmations` with dates/source context.
- Re-import the sidecar. The loader replaces child rows for the same `encounter_id`, so stale medication/fact rows are removed.
- Use `skills/dossier-sync` before updating dossier Markdown. Update only when corrected facts affect current medications, past medications, timeline events, active concerns, visit summaries, or doctor-facing questions.

## Sidecar Shape

Use one JSON object per encounter:

```json
{
  "schema_version": "1",
  "parser_version": "manual-ai-2026-04-21",
  "encounter_id": "2026-04-21-prescription-ab12cd34",
  "source_files": [
    {
      "path": "/absolute/path/to/people/<person-slug>/prescriptions/raw/2026-04-21-prescription-ab12cd34/PHOTO.jpg",
      "sha256": "",
      "original_name": "PHOTO.jpg",
      "file_type": "image/jpeg",
      "page_order": 1,
      "notes": ""
    }
  ],
  "source_manifest_sha256": "",
  "sidecar_path": "/absolute/path/to/people/<person-slug>/prescriptions/sidecars/2026-04-21-prescription-ab12cd34.prescription.json",
  "ingested_at": "2026-04-21T00:00:00+00:00",
  "last_reprocessed_at": "",
  "reprocess_reason": "",
  "patient_name": "",
  "prescription_date": "YYYY-MM-DD",
  "prescription_date_text": "",
  "prescriber": "",
  "clinic": "",
  "status": "needs_user_review",
  "warnings": [],
  "unresolved_questions": [],
  "user_confirmations": [],
  "pages": [],
  "medication_orders": [],
  "clinical_facts": []
}
```

Each `pages` entry should use:

```json
{
  "page": 1,
  "source_file": "/absolute/path/to/source.jpg",
  "source_page": null,
  "readability": "clear | partial | poor | unreadable",
  "notes": "",
  "warnings": []
}
```

Each `medication_orders` entry should use:

```json
{
  "raw_name": "",
  "normalized_name": "",
  "strength": "",
  "dose": "",
  "route": "",
  "frequency": "",
  "timing": "",
  "duration": "",
  "quantity": "",
  "action": "start | continue | stop | change | unknown",
  "indication": "",
  "confidence": 0.8,
  "needs_review": true,
  "source_page": 1,
  "source_file": "/absolute/path/to/source.jpg",
  "raw_visual_note": "",
  "warnings": []
}
```

Each `clinical_facts` entry should use:

```json
{
  "fact_type": "diagnosis | symptom | vital | test_advised | lifestyle_advice | follow_up | referral | note | doctor_question | other",
  "label": "",
  "value_text": "",
  "normalized_value": "",
  "confidence": 0.8,
  "needs_review": false,
  "source_page": 1,
  "source_file": "/absolute/path/to/source.jpg",
  "raw_visual_note": "",
  "warnings": []
}
```

## Manual Extraction Rules

- Preserve the prescription wording when it is readable. Put interpretation or normalized names in separate fields.
- For medicine-name verification, use online sources only as cross-checks for
  likely product/generic identity and composition. Note the prescription
  context that connects the medicine to the encounter, such as diagnosis,
  symptom, procedure, or doctor instruction, and keep unclear clinical purpose
  as an open question.
- Use `action: "unknown"` when the prescription does not clearly say whether a medicine is new, continued, stopped, or changed.
- Keep ambiguous drug names as the visible text plus `needs_review: true`; do not silently choose a likely medicine.
- Keep uncertain shorthand such as `1-0-1`, `BD`, `HS`, or `SOS` in the relevant raw fields unless the user confirms the meaning.
- Capture vitals, advised tests, follow-up timing, and lifestyle instructions as `clinical_facts`, not medication rows.
- Keep unresolved user questions in the sidecar only. Do not copy them to `questions-for-doctor.md` unless the user confirms they are doctor-facing.
- Do not infer diagnoses or medication indications unless the prescription explicitly states them or the user confirms them.

## SQLite Loading

The helper script imports reviewed sidecars only. It does not accept source images or PDFs as input and does not extract prescription content.

See `references/sqlite-schema.md` for the schema and query examples.

Useful review query:

```sql
select prescription_date, raw_name, dose, frequency, duration, raw_visual_note
from medication_orders
join prescription_encounters using (encounter_id)
where medication_orders.needs_review = 1
   or prescription_encounters.status in ('needs_review', 'needs_user_review')
order by prescription_date, raw_name;
```
