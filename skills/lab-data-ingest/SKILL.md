---
name: lab-data-ingest
description: Manually extract structured lab values from medical lab report PDFs, images, text files, CSV/TSV, and spreadsheets into JSON sidecars and a SQLite database. Use when Codex needs to ingest a person's lab reports by extracting each page's text, manually reading page-by-page content, preserving units/reference ranges, creating searchable local records, or preparing lab data for trend analytics without relying on automated value parsing.
---

# Lab Data Ingest

## Core Rule

Extract lab values yourself as the AI agent, page by page. Start by extracting text from each PDF page separately, then manually read that page text and transcribe the values. Do not use code, regexes, OCR tables, or parser heuristics to decide which lab tests, values, units, flags, or reference ranges are present.

Code is allowed only for mechanical support:

- listing files and counting pages
- extracting text page by page for manual AI review
- rendering pages to images for visual checks
- hashing source files
- validating JSON syntax and schema shape
- loading an already AI-reviewed sidecar into SQLite
- running analytics queries after ingestion

Treat extracted text, OCR, CSV rows, and spreadsheet cells as source material for manual AI review, not as automated parsing output. If the page text is incomplete, garbled, reordered, missing units/ranges, or inconsistent with the page image, try other local methods before finalizing: render the page image, use OCR, inspect spreadsheet cells, crop/zoom the page, or compare against another copy of the report.

## Workflow

Use this skill for folder-local, person-scoped lab ingestion.

1. Place new unsorted source files in `people/<person-slug>/raw-data-dump/` and classify them before extraction.
2. Work in small batches: usually one lab report at a time, or a tightly related
   set of reports when the dates and source context are clear.
3. For each report, identify page count and extract text page by page.
4. Manually inspect the extracted text for page 1, then page 2, continuing sequentially through the report.
5. For pages where extracted text is blank, garbled, visually suspicious, or clinically important, try another local view: render the page, crop/zoom it, OCR it, or inspect the original file another way.
6. Manually transcribe each lab result into a JSON sidecar under `people/<person-slug>/labs/sidecars/`.
7. Mark uncertainty with `needs_review: true`, lower `confidence`, and a warning. Do not guess missing units or ranges.
8. Pause before import when patient identity, report date, units, reference
   ranges, duplicate status, or clinically important values are ambiguous.
   Summarize the ambiguity and ask the user one focused review batch.
9. Validate the sidecar JSON mechanically and spot-check suspicious rows against the best available page view.
10. After the manual extraction is verified, move the original lab report out of `people/<person-slug>/raw-data-dump/` into `people/<person-slug>/labs/raw/` if it is still in the intake folder.
11. Update the sidecar `source_file` and `source_sha256` to the final `people/<person-slug>/labs/raw/` path after moving the source file.
12. Load the reviewed sidecar into `people/<person-slug>/labs/labs.sqlite` only after the manual extraction is complete and the sidecar points at the final source path.
13. Do not delete, overwrite, or modify source reports.
14. Before updating dossier Markdown from lab results, use `skills/dossier-sync` and its confirmed-facts-only rules. Keep uncertain rows in sidecars/SQLite review queues unless the dossier explicitly needs a marked open question.
15. After each batch, report the source files handled, sidecars written, SQLite
    import status, rows kept in review, and the next proposed lab batch.

## Page-By-Page Extraction

For every page, first produce page-separated text, then read it manually. Capture enough provenance to let a later reviewer find the value:

- `page`: PDF page number or sheet/page number.
- `line_number`: use `null` if line numbers are not stable.
- `raw_line`: short source text around the result, copied from the page text or typed from the page view after manual review.
- `warnings`: note page-level problems such as blank text extraction, garbled ordering, cropped text, faint print, ambiguous columns, OCR mismatch, split tables, or page image rendering problems.

When a page has no lab values, record that in your working notes. You do not need to create empty result rows for non-lab pages.

If text extraction and visual rendering disagree, do not force a clean result. Use the most reliable local method available, mark affected rows `needs_review: true`, and include the disagreement in `warnings`.

## Manual Result Rules

For each result:

- Preserve the displayed test name, value text, unit, reference range, and flag.
- Keep original units. Do not silently convert.
- Put numeric values in both `value_text` and `value_numeric` when the report shows a clean number.
- Use `value_numeric: null` for qualitative results, ranges, ratios with nonstandard notation, or unclear values.
- Use `flag` only when the report explicitly flags the value or the reference range makes the interpretation unambiguous.
- Use `flag: "unknown"` when interpretation depends on age, sex, cycle day, pregnancy status, lab method, or category bands.
- Keep comments, methods, specimen type, and clinical notes out of `test_name`; put them in `specimen`, `raw_line`, or warnings.
- Do not infer diagnoses from lab values during ingestion.

Allowed flags: `low`, `normal`, `high`, `critical`, `abnormal`, `unknown`.

## Sidecar Shape

Create one JSON sidecar per source file. Use this shape:

```json
{
  "schema_version": "1",
  "parser_version": "manual-ai-2026-04-20",
  "source_file": "/absolute/path/to/people/<person-slug>/labs/raw/report.pdf",
  "source_sha256": "...",
  "sidecar_path": "/absolute/path/to/people/<person-slug>/labs/sidecars/report-hash.labs.json",
  "ingested_at": "2026-04-20T00:00:00+00:00",
  "patient_name": "",
  "report_date": "YYYY-MM-DD",
  "report_date_text": "",
  "status": "ok",
  "warnings": [],
  "result_count": 0,
  "needs_review_count": 0,
  "results": []
}
```

Each `results` entry must use:

```json
{
  "test_name": "",
  "normalized_test_name": "",
  "value_text": "",
  "value_numeric": null,
  "unit": "",
  "reference_range": "",
  "flag": "unknown",
  "specimen": "",
  "category": "",
  "page": 1,
  "line_number": null,
  "confidence": 0.9,
  "needs_review": false,
  "raw_line": ""
}
```

Set `status` to `needs_review` if any result needs review or the report has extraction warnings. Set `status` to `no_text` only when no readable content can be obtained and manual page viewing also cannot recover values.

## Quick Mechanical Helpers

Use Python or shell for quick support tasks only. Examples:

```bash
.venv/bin/python -m json.tool people/example-person/labs/sidecars/example.labs.json >/tmp/validated-labs.json
```

```bash
shasum -a 256 people/example-person/labs/raw/example.pdf
```

For PDF text extraction, use page-separated output so the AI can review one page at a time. For example, with `pypdf`, print a clear `--- PAGE n ---` marker before each page's text.

If page images are needed, render pages to a temporary directory and inspect them one at a time. OCR output may be used as another page-level source for manual review, but not as an automated result parser.

## SQLite Loading And Analytics

Use SQLite for trends after sidecars are manually reviewed. See `references/sqlite-schema.md` for the schema and example queries.

The helper script imports already-reviewed sidecars only. It does not accept source reports or extract lab values:

```bash
.venv/bin/python skills/lab-data-ingest/scripts/ingest_labs.py people/example-person/labs/sidecars --recursive
```

Useful query pattern:

```sql
select
  coalesce(report_date, ingested_at) as date,
  test_name,
  value_numeric,
  unit,
  reference_range,
  flag,
  source_path
from lab_results
join reports on reports.id = lab_results.report_id
where normalized_test_name like '%hba1c%'
order by date;
```

## Review Before Use

Before using values analytically:

- Verify patient identity if multiple people could appear in the source folder.
- Verify report date, collection date, units, reference ranges, and abnormal flags.
- Compare suspicious or clinically important values against the page image.
- Preserve uncertainty. Mark unclear rows as `needs_review`, not as clean facts.
- Use `skills/dossier-sync` before copying any lab-derived summary into `timeline.md`, `current-concerns.md`, `questions-for-doctor.md`, or appointment summaries.
