---
name: medication-image-ingest
description: Manually ingest a person's medicine package, blister-strip, bottle, vial, label, or pharmacy sticker photos into one JSON sidecar per product capture and a searchable SQLite index. Use when Codex needs to identify medicine names from package images, verify likely product/generic/composition online, tie the product to the correct person, cross-check schedule and current-use details against existing records before asking the user, or reprocess a previously ingested medication-image capture without relying on automated medicine-name parsing.
---

# Medication Image Ingest

## Core Rule

Manually read the medicine images yourself as the AI agent. Use zooming,
rotation, contrast adjustments, local OCR, or alternate views only to improve
readability. Do not use automated OCR or heuristics as the final authority for
the medicine name, strength, schedule, or patient-specific status.

This skill is for medicine-product evidence, not for doctor prescriptions as
clinical encounters. Use `skills/prescription-data-ingest` when the source is a
prescription page. Use this skill when the source is the actual medicine
package, blister strip, bottle, vial, pharmacy label, or sticker.

Treat online sources as product-identity support, not as permission to invent a
patient-specific schedule. Patient-specific dosing and active-vs-past status
must come from the package image itself, existing dossier records, prescription
records, or explicit user confirmation.

## Workflow

1. Start from `people/<person-slug>/raw-data-dump/` and confirm the active
   person before moving files.
2. Work in small batches: one physical medicine product, package, strip,
   bottle, vial, sticker, or tightly related capture session at a time.
3. Classify incoming files. If a file is a prescription, send it to
   `skills/prescription-data-ingest` instead of this skill.
4. If product grouping, active person, duplicate status, whether the file is a
   prescription vs medicine image, or whether images show the same variant is
   unclear, stop before moving/importing and ask the user a focused review
   question.
5. Group all images/pages that show the same physical medicine product or the
   same package capture session. Create one sidecar per grouped product capture.
6. Move grouped originals to
   `people/<person-slug>/medication-images/raw/<capture-id>/`. Preserve
   original filenames.
7. Manually inspect each source page/image in order. Record readability,
   cropped text, hidden strength lines, partially visible manufacturer text,
   and whether the image shows front, back, side panel, blister, or sticker.
8. Extract only what is actually visible: product name, generic or composition
   text, dosage form, strength, route, manufacturer, schedule stickers, refill
   labels, expiry, or other package text.
9. Before asking the user anything, search the active person's current records
   for the same or a likely matching medicine. Check at least:
   - `people/<person-slug>/medications.md`
   - `people/<person-slug>/timeline.md`
   - `people/<person-slug>/current-concerns.md`
   - `people/<person-slug>/prescriptions/prescriptions.sqlite`
   - `people/<person-slug>/prescriptions/sidecars/`
   - prior `people/<person-slug>/medication-images/sidecars/` or
     `medication_images.sqlite` if they exist
   - recent visit notes or summaries when they are likely to mention the same
     medicine
10. Build the best record-backed draft before interacting with the user. Print a
   concise pre-question summary that shows:
   - what medicine name the image most likely shows
   - which existing records match it
   - the best schedule already supported by records
   - whether the image appears to show a different variant than the record, for
     example `SR`, `CR`, `ER`, `OD`, `Forte`, `Plus`, combination-strength, or
     pediatric/ophthalmic variant differences
   - what still remains ambiguous
11. Search online to verify likely product identity and composition. Prefer
   authoritative sources in this order:
   - official label or manufacturer page
   - government or regulator source when available
   - DailyMed for products with U.S. label coverage
   - reputable medicine compendium only when better sources are unavailable
12. Record the online sources used, access date, matched product text, and what
    they support. Do not let web results override illegible image text,
    patient-specific dosing, or the person linkage.
13. Ask the user only for the remaining ambiguities in one focused review batch:
    - unclear product name if the image plus record search is still not enough
    - whether the product really belongs to the active person if that remains
      uncertain
    - schedule or current-use confirmation only if current records do not
      already settle it
14. Write one JSON sidecar under
    `people/<person-slug>/medication-images/sidecars/` with suffix
    `.medication-image.json`.
15. Validate the sidecar JSON mechanically, then import it into SQLite:

```bash
.venv/bin/python skills/medication-image-ingest/scripts/ingest_medication_images.py people/example-person/medication-images/sidecars --recursive
```

16. Before updating dossier Markdown, use `skills/dossier-sync`. Sync only
    confirmed medication facts into `medications.md`, `timeline.md`,
    `current-concerns.md`, visit notes, or doctor-facing questions.
17. After each batch, report the source files handled, capture ID, sidecar path,
    SQLite import status, unresolved questions, and the next proposed medication
    image batch.

## Duplicate Handling

- Treat exact duplicate files as the same source when `sha256` matches an
  existing medication-image source file.
- Treat exact duplicate grouped captures as the same capture when the ordered
  `source_manifest_sha256` matches an existing capture.
- Also treat non-identical photos as the same capture when manual review shows
  they are the same front/back/side of the same product package or a clearer
  recapture of an existing image.
- If a new image is clearly a better photo of an already ingested product
  capture, reprocess the existing capture instead of creating a second one.

## Reprocessing

Reprocess a capture when the user supplies missing details, a clearer package
photo arrives, the online match looks wrong, or the person-specific schedule
needs correction.

- Re-read the originals from
  `people/<person-slug>/medication-images/raw/<capture-id>/`.
- Overwrite the current sidecar for that capture; do not create archived
  sidecar revisions by default.
- Preserve `capture_id`, update `last_reprocessed_at`, and write a short
  `reprocess_reason`.
- Add user-provided corrections to `user_confirmations` with dates and source
  context.
- Re-import the sidecar. The loader replaces child rows for the same
  `capture_id`, so the SQLite index reflects the latest sidecar and summary
  values.
- Use `skills/dossier-sync` before updating dossier Markdown. Update only when
  the corrected fact changes the active medication list, past medication
  history, current concerns, or timeline.

## Existing-Record Search Before User Questions

Before you ask the user anything, do a person-local search first.

- Search exact and fuzzy variants of the visible name, including brand and
  generic text. Example: if the strip seems to say `Aten D`, also search for
  `aten d`, `aten`, and the generic combination if visible.
- Prefer the active person's most recent medication record over older matches.
- If multiple prior records disagree, surface the conflict in the pre-question
  summary instead of hiding it.
- If the package image appears to show a different variant than the existing
  record, do not silently merge them under the same medicine. Treat the
  discrepancy as unresolved until you determine whether it is:
  - a real medication change
  - a stronger or weaker strength of the same product
  - a different release formulation such as `SR` or `CR`
  - a different composition or combination product
  - a record mistake or older historical variant
- If a schedule is already clearly documented in a current record, present that
  schedule back to the user for confirmation only when needed for unresolved
  conflict. Do not ask them to restate information already settled by current
  records.
- When you must ask for confirmation, include clickable local file links to the
  exact supporting record or image path in your user-facing message.

## Online Verification Rules

- Use the package image text as the anchor. Online search exists to confirm the
  likely product, not to replace unreadable text with a guess.
- Record the product facts that the source supports: generic name,
  composition, dosage form, strength family, route, variant, and common labeled
  use.
- Search online for the exact visible variant, not just the base brand name, so
  the sidecar records the best-supported composition for later analysis.
- Do not use online results to infer that the patient currently takes the
  medicine, how often they take it, or why they take it unless a local record
  confirms that context.
- If only low-quality commercial listings are available, note that limitation
  in `warnings` and keep `needs_name_confirmation` true when appropriate.

## Sidecar Shape

Create one JSON sidecar per grouped product capture:

```json
{
  "schema_version": "1",
  "parser_version": "manual-ai-2026-05-14",
  "capture_id": "2026-05-14-medication-image-cardirose-e4f3a2b1",
  "person_slug": "person-slug",
  "source_files": [
    {
      "path": "/absolute/path/to/people/<person-slug>/medication-images/raw/2026-05-14-medication-image-cardirose-e4f3a2b1/IMG_0001.JPG",
      "sha256": "",
      "original_name": "IMG_0001.JPG",
      "file_type": "image/jpeg",
      "page_order": 1,
      "notes": "Front of strip"
    }
  ],
  "source_manifest_sha256": "",
  "sidecar_path": "/absolute/path/to/people/<person-slug>/medication-images/sidecars/2026-05-14-medication-image-cardirose-e4f3a2b1.medication-image.json",
  "ingested_at": "2026-05-14T00:00:00+00:00",
  "last_reprocessed_at": "",
  "reprocess_reason": "",
  "capture_date": "YYYY-MM-DD",
  "capture_date_text": "",
  "status": "needs_user_review",
  "warnings": [],
  "unresolved_questions": [],
  "user_confirmations": [],
  "pages": [],
  "identified_medications": []
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

Each `identified_medications` entry should use:

```json
{
  "raw_name": "",
  "normalized_name": "",
  "variant": "",
  "generic_name": "",
  "strength": "",
  "dosage_form": "",
  "route": "",
  "manufacturer": "",
  "pack_size": "",
  "composition": "",
  "common_uses": [],
  "record_match_summary": "",
  "schedule_from_records": "",
  "current_status_from_records": "",
  "name_confidence": 0.8,
  "schedule_confidence": 0.0,
  "needs_name_confirmation": true,
  "needs_schedule_confirmation": false,
  "source_page": 1,
  "source_file": "/absolute/path/to/source.jpg",
  "raw_visual_note": "",
  "warnings": [],
  "record_matches": [],
  "online_matches": []
}
```

Each `record_matches` entry should use:

```json
{
  "record_type": "medications_md | timeline_md | current_concerns_md | prescription_sidecar | prescription_sqlite | visit_note | summary | prior_medication_image | other",
  "record_path": "/absolute/path/to/supporting/file-or-db",
  "record_date": "YYYY-MM-DD",
  "matched_name": "",
  "schedule_text": "",
  "status_text": "",
  "notes": ""
}
```

Each `online_matches` entry should use:

```json
{
  "source_type": "official_label | manufacturer | regulator | compendium | other",
  "source_name": "",
  "url": "https://example.com",
  "accessed_at": "YYYY-MM-DD",
  "matched_name": "",
  "generic_or_composition": "",
  "notes": ""
}
```

## Manual Extraction Rules

- Preserve the visible package wording in `raw_name` and `raw_visual_note`.
- Preserve visible variant markers such as `SR`, `CR`, `ER`, `OD`, `MR`,
  `Forte`, `Plus`, or combination suffixes in `variant` when present.
- Keep brand-name interpretation, generic identity, and composition in separate
  fields.
- If the image variant differs from the best current record match, keep both
  versions explicit, set `needs_name_confirmation: true`, and add an unresolved
  question rather than collapsing them into one assumed product.
- Use `needs_name_confirmation: true` when the product name is still uncertain
  after image review, record search, and online cross-check.
- Use `needs_schedule_confirmation: true` only when current records do not
  settle the patient-specific schedule or current-use status.
- Keep packaging facts and product identity separate from user-reported
  adherence or treatment response.
- Do not infer the person's diagnosis or reason for use from internet results
  alone.
- Do not delete uncertainty just because the likely match seems obvious.

## SQLite Loading

The helper script imports reviewed sidecars only. It does not parse medicine
images, search the internet, or determine schedules automatically. It keeps a
lightweight one-row-per-sidecar SQLite index rather than a large normalized
schema.

See `references/sqlite-schema.md` for the schema and query examples.

Useful review query:

```sql
select
  c.capture_date,
  m.raw_name,
  m.normalized_name,
  m.schedule_from_records,
  m.current_status_from_records,
  m.needs_name_confirmation,
  m.needs_schedule_confirmation
from identified_medications m
join medication_image_captures c using (capture_id)
where m.needs_name_confirmation = 1
   or m.needs_schedule_confirmation = 1
   or c.status in ('needs_review', 'needs_user_review')
order by c.capture_date, m.raw_name;
```

## Final Review Before User Interaction

Before you ask the user for clarification:

- Re-read the image snippets that created the ambiguity.
- Re-check the person-local records for a matching medicine and schedule.
- Summarize the best current understanding first.
- Ask only the narrow remaining questions.

This skill should reduce user burden, not move routine cross-checking onto the
user.
