# SQLite Schema

The medication-image importer is intentionally minimal:

```bash
.venv/bin/python skills/medication-image-ingest/scripts/ingest_medication_images.py people/example-person/medication-images/sidecars --recursive
```

It stores one row per sidecar. The sidecar JSON remains the source of truth.
SQLite is only a lightweight search and review index.

The script opens SQLite with WAL mode, `busy_timeout = 5000`, and
`synchronous = normal`.

## `medication_image_captures`

One row per medication-image sidecar.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `capture_id` | text unique | Stable capture id from the sidecar |
| `person_slug` | text | Person folder slug tied to the capture |
| `source_manifest_sha256` | text | Hash of ordered source file paths and hashes |
| `sidecar_path` | text | JSON sidecar path |
| `capture_date` | text | Normalized `YYYY-MM-DD` when known |
| `capture_date_text` | text | Raw date text |
| `ingested_at` | text | Sidecar ingestion timestamp |
| `last_reprocessed_at` | text | Empty unless reprocessed |
| `reprocess_reason` | text | Short reason for latest reprocess |
| `parser_version` | text | Manual extraction version |
| `status` | text | `ok`, `needs_review`, `needs_user_review`, or `no_readable_content` |
| `raw_names_json` | text | JSON array of visible medicine names |
| `normalized_names_json` | text | JSON array of normalized names |
| `variants_json` | text | JSON array of visible variants such as `SR`, `CR`, `Forte` |
| `compositions_json` | text | JSON array of recorded compositions |
| `needs_name_confirmation_count` | integer | Count of medication rows still needing name confirmation |
| `needs_schedule_confirmation_count` | integer | Count of medication rows still needing schedule confirmation |
| `warnings_json` | text | JSON array |
| `unresolved_questions_json` | text | JSON array |
| `user_confirmations_json` | text | JSON array |
| `source_files_json` | text | JSON array |
| `pages_json` | text | JSON array copied from the sidecar |
| `identified_medications_json` | text | JSON array copied from the sidecar |
| `sidecar_json` | text | Full sidecar JSON blob |
| `imported_at` | text | Import timestamp |

## Reprocessing Behavior

The loader upserts by `capture_id`. Re-importing a corrected sidecar replaces
the single indexed row with the latest summary values and full JSON payload.

## Example Queries

Rows needing user confirmation:

```sql
select
  capture_date,
  status,
  raw_names_json,
  normalized_names_json,
  variants_json,
  needs_name_confirmation_count,
  needs_schedule_confirmation_count
from medication_image_captures
where status in ('needs_review', 'needs_user_review')
   or needs_name_confirmation_count > 0
   or needs_schedule_confirmation_count > 0
order by capture_date;
```

Find a medicine or variant:

```sql
select
  capture_date,
  raw_names_json,
  normalized_names_json,
  variants_json,
  compositions_json,
  sidecar_path
from medication_image_captures
where lower(normalized_names_json) like '%cardirose%'
   or lower(raw_names_json) like '%cardirose%'
   or lower(variants_json) like '%sr%'
order by capture_date;
```

Find composition matches for later analysis:

```sql
select
  capture_date,
  normalized_names_json,
  compositions_json,
  sidecar_path
from medication_image_captures
where lower(compositions_json) like '%metformin%'
order by capture_date;
```
