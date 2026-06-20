# SQLite Schema

The imaging ingestion script creates this database if missing:

```bash
.venv/bin/python skills/imaging-data-ingest/scripts/ingest_imaging.py people/example-person/imaging/sidecars --recursive
```

The script opens SQLite with WAL mode, `busy_timeout = 5000`, `synchronous =
normal`, and `foreign_keys = on`.

## `imaging_studies`

One row per imaging/procedure sidecar.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `study_id` | text unique | Stable study/procedure id from the sidecar |
| `source_manifest_sha256` | text | Hash of ordered source file paths and hashes |
| `sidecar_path` | text | JSON sidecar path |
| `patient_name` | text | Extracted if visible |
| `study_date` | text | Normalized `YYYY-MM-DD` when known |
| `study_date_text` | text | Raw date text |
| `facility` | text | Imaging center, hospital, or clinic |
| `referring_doctor` | text | Referring doctor text |
| `performing_doctor` | text | Radiologist/proceduralist text |
| `modality` | text | `ultrasound`, `xray`, `mri`, `ct`, `procedure`, or `unknown` |
| `body_part` | text | Body part or region |
| `laterality` | text | `left`, `right`, `bilateral`, `midline`, `not_applicable`, or `unknown` |
| `study_type` | text | `diagnostic`, `procedure`, `mixed`, or `unknown` |
| `ingested_at` | text | Sidecar ingestion timestamp |
| `last_reprocessed_at` | text | Empty unless reprocessed |
| `reprocess_reason` | text | Short reason for latest reprocess |
| `parser_version` | text | Manual extraction version |
| `status` | text | `ok`, `needs_review`, `needs_user_review`, or `no_readable_content` |
| `warnings_json` | text | JSON array |
| `unresolved_questions_json` | text | JSON array |
| `user_confirmations_json` | text | JSON array |
| `source_files_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## `imaging_pages`

One row per image/PDF page reviewed for the study.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `study_id` | text | Foreign key |
| `page` | integer | Study page order |
| `source_file` | text | Source path |
| `source_page` | integer | PDF/source page when applicable |
| `readability` | text | `clear`, `partial`, `poor`, or `unreadable` |
| `notes` | text | Page-level notes |
| `warnings_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## `imaging_findings`

One row per extracted imaging/procedure fact.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `study_id` | text | Foreign key |
| `finding_index` | integer | Sidecar list index |
| `finding_type` | text | `indication`, `technique`, `finding`, `impression`, `measurement`, `procedure_detail`, `injected_medication`, `recommendation`, `comparison`, `note`, or `other` |
| `label` | text | Fact label |
| `value_text` | text | Preserved report/procedure text |
| `normalized_value` | text | Normalized value when useful |
| `confidence` | real | Manual extraction confidence |
| `needs_review` | integer | `1` if the row needs review |
| `source_page` | integer | Study page order |
| `source_file` | text | Source path |
| `raw_visual_note` | text | Short visual/source note |
| `warnings_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## Reprocessing Behavior

The loader upserts `imaging_studies` by `study_id`, then deletes and reinserts
all page and finding rows for that study. Re-importing a corrected sidecar
therefore removes stale child rows.

## Example Queries

Rows needing review:

```sql
select s.study_date, s.status, s.modality, s.body_part, f.finding_type, f.label, f.value_text
from imaging_findings f
join imaging_studies s using (study_id)
where s.status in ('needs_review', 'needs_user_review')
   or f.needs_review = 1
order by s.study_date, f.finding_index;
```

Shoulder imaging/procedure timeline:

```sql
select s.study_date, s.study_type, s.modality, s.laterality, s.body_part, f.finding_type, f.value_text
from imaging_findings f
join imaging_studies s using (study_id)
where lower(s.body_part) like '%shoulder%'
order by s.study_date, f.finding_index;
```

Injected medicines:

```sql
select s.study_date, s.facility, s.performing_doctor, f.value_text, f.raw_visual_note
from imaging_findings f
join imaging_studies s using (study_id)
where f.finding_type = 'injected_medication'
order by s.study_date;
```
