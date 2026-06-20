---
name: imaging-data-ingest
description: Manually ingest a person's imaging, procedure, and radiology reports into JSON sidecars and a searchable SQLite index. Use when Codex needs to classify imaging/procedure files from a person-local raw intake folder, extract modality, body part, laterality, findings, impression, procedure details, injected medicines, measurements, recommendations, or reprocess a reviewed imaging record without relying on automated radiology parsing.
---

# Imaging Data Ingest

## Core Rule

Manually read imaging and procedure records yourself as the AI agent. Use image
viewing, local PDF text extraction, zooming, rotation, contrast checks, or OCR
only as readability support. Do not use code, OCR, regexes, or parser heuristics
to decide which findings, measurements, impressions, diagnoses, medicines, or
procedure details are present.

Capture uncertainty plainly. Do not convert an imaging impression into a
diagnosis unless the report explicitly states it. Keep unclear laterality,
modality, injected medicine, dose, site, or date as review/user questions.

If anything material is ambiguous after reading the images, continue the
read/draft pass, collect all uncertainties in `unresolved_questions`, and ask
the user one focused batch of questions at the end before finalizing the sidecar
or importing it into SQLite. Request supporting data if available. Examples
include unclear handwriting, uncertain medicine names or doses, uncertain
procedure site, laterality conflicts, date conflicts, cropped
findings/impressions, or whether a record belongs to the same encounter.

## Workflow

1. Start from `people/<person-slug>/raw-data-dump/` and classify files before
   extraction.
2. Work in small batches: one imaging study or procedure encounter at a time,
   or a tightly related multi-page study when all pages clearly belong
   together.
3. Before creating a new study, compare each raw file against already ingested
   imaging/prescription records in two ways:
   first by source hashes/manifests when available, and then by manual content
   review of date, doctor, laterality, body part, visible wording, page layout,
   handwriting, and whether the image is the front/back or a clearer recapture
   of an existing page. If the file belongs to an existing study, do not create
   a new study. Reprocess the existing study instead, or leave the duplicate in
   intake until the user says whether to discard it.
4. If study grouping, duplicate status, patient identity, date, laterality,
   body part, or whether a file is imaging vs prescription is unclear, stop
   before moving/importing and ask the user a focused review question.
5. Group all images/pages from the same imaging study or procedure encounter.
6. Move grouped originals to `people/<person-slug>/imaging/raw/<study-id>/`.
   Preserve original filenames when useful.
7. Manually inspect each source page/image in order. Record readability issues,
   cropped areas, handwriting ambiguity, page overlap, and alternate local views
   used.
8. Draft one JSON sidecar under `people/<person-slug>/imaging/sidecars/` with
   suffix `.imaging.json`.
9. If important details are unclear, draft them in `unresolved_questions`, set
   `status: "needs_user_review"`, and keep reading the remaining pages/files.
   Do not silently choose a likely interpretation. Ask the user in one focused
   review batch before final import or dossier sync.
10. After user verification, incorporate answers into `user_confirmations`. If
   ambiguity remains, keep the uncertain rows marked `needs_review: true`.
11. Validate the sidecar JSON mechanically, then import it into SQLite:

```bash
.venv/bin/python skills/imaging-data-ingest/scripts/ingest_imaging.py people/example-person/imaging/sidecars --recursive
```

12. Before updating dossier Markdown from imaging results, use
   `skills/dossier-sync` and its confirmed-facts-only rules. Update
   `timeline.md`, `current-concerns.md`, visit notes, or summaries only when
   facts are confirmed or explicitly marked as open questions.
13. After each batch, report the source files handled, study ID, sidecar path,
    SQLite import status, unresolved questions, and the next proposed imaging
    batch.

## Duplicate Handling

- Treat exact duplicate files as the same source when `sha256` matches an
  existing ingested source file.
- Treat exact duplicate multi-file studies as the same study when the ordered
  `source_manifest_sha256` matches an existing ingested study.
- Also treat non-identical photos as the same source when manual review shows
  they are the same clinical page, the back side of an already ingested page,
  or a clearer/recropped version of an existing image.
- If a new image is not byte-identical but is clearly a better photo of the
  same page or encounter, reprocess the existing study instead of creating a
  second study for the same event.
- Keep duplicate warnings in the sidecar/import output so future agents can see
  why a record was merged or held for review.

## Reprocessing

Reprocess a study when the user supplies missing details, a better image
arrives, a prior read looks wrong, or clinical interpretation needs correction.

- Re-read the original files from `people/<person-slug>/imaging/raw/<study-id>/`.
- Overwrite the current sidecar for that study; do not create archived sidecar
  revisions by default.
- Preserve `study_id`, update `last_reprocessed_at`, and write a short
  `reprocess_reason`.
- Add user-provided corrections to `user_confirmations` with dates/source
  context.
- Re-import the sidecar. The loader replaces child rows for the same
  `study_id`, so stale page and finding rows are removed.

## Sidecar Shape

Use one JSON object per imaging study or procedure:

```json
{
  "schema_version": "1",
  "parser_version": "manual-ai-2026-05-12",
  "study_id": "2025-12-11-right-shoulder-sonography-ab12cd34",
  "source_files": [
    {
      "path": "/absolute/path/to/people/<person-slug>/imaging/raw/<study-id>/IMG_0001.JPG",
      "sha256": "",
      "original_name": "IMG_0001.JPG",
      "file_type": "image/jpeg",
      "page_order": 1,
      "notes": ""
    }
  ],
  "source_manifest_sha256": "",
  "sidecar_path": "/absolute/path/to/people/<person-slug>/imaging/sidecars/<study-id>.imaging.json",
  "ingested_at": "2026-05-12T00:00:00+00:00",
  "last_reprocessed_at": "",
  "reprocess_reason": "",
  "patient_name": "",
  "study_date": "YYYY-MM-DD",
  "study_date_text": "",
  "facility": "",
  "referring_doctor": "",
  "performing_doctor": "",
  "modality": "ultrasound | xray | mri | ct | procedure | unknown",
  "body_part": "",
  "laterality": "left | right | bilateral | midline | not_applicable | unknown",
  "study_type": "diagnostic | procedure | mixed | unknown",
  "status": "needs_user_review",
  "warnings": [],
  "unresolved_questions": [],
  "user_confirmations": [],
  "pages": [],
  "findings": []
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

Each `findings` entry should use:

```json
{
  "finding_type": "indication | technique | finding | impression | measurement | procedure_detail | injected_medication | recommendation | comparison | note | other",
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

- Preserve the report's wording for findings and impressions.
- Store injected medicines as `finding_type: "injected_medication"` unless the
  record is a prescription order.
- Store measurements, thicknesses, and lesion sizes as `measurement` findings
  with the original unit.
- Keep the report's laterality exactly when stated. If the image overlay and
  paper report disagree, mark `needs_review`.
- Reverify ambiguous report text, handwriting, medicine names, doses, procedure
  sites, laterality, and dates with the user in one focused batch after the
  read/draft pass, before treating them as confirmed.
- Do not infer current symptom severity or treatment success from imaging alone.
- Do not infer diagnoses from normal/abnormal imaging unless the report states
  them in the findings or impression.

## SQLite Loading

The helper script imports reviewed sidecars only. It does not accept source
images or PDFs as input and does not extract imaging content.

See `references/sqlite-schema.md` for the schema and query examples.
