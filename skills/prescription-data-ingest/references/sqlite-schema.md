# SQLite Schema

The prescription ingestion script creates this database if missing:

```bash
.venv/bin/python skills/prescription-data-ingest/scripts/ingest_prescriptions.py people/example-person/prescriptions/sidecars --recursive
```

The script opens SQLite with WAL mode, `busy_timeout = 5000`, `synchronous = normal`, and `foreign_keys = on`.

## `prescription_encounters`

One row per prescription sidecar.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `encounter_id` | text unique | Stable encounter id from the sidecar |
| `source_manifest_sha256` | text | Hash of ordered source file paths and hashes |
| `sidecar_path` | text | JSON sidecar path |
| `patient_name` | text | Extracted if visible |
| `prescription_date` | text | Normalized `YYYY-MM-DD` when known |
| `prescription_date_text` | text | Raw date text |
| `prescriber` | text | Doctor/prescriber text |
| `clinic` | text | Clinic/facility text |
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

## `prescription_pages`

One row per image/PDF page reviewed for the encounter.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `encounter_id` | text | Foreign key |
| `page` | integer | Encounter page order |
| `source_file` | text | Source path |
| `source_page` | integer | PDF/source page when applicable |
| `readability` | text | `clear`, `partial`, `poor`, or `unreadable` |
| `notes` | text | Page-level notes |
| `warnings_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## `medication_orders`

One row per medication instruction.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `encounter_id` | text | Foreign key |
| `order_index` | integer | Sidecar list index |
| `raw_name` | text | Medicine name exactly as read |
| `normalized_name` | text | Normalized name when clear |
| `strength` | text | Strength text |
| `dose` | text | Dose text |
| `route` | text | Route text |
| `frequency` | text | Frequency text |
| `timing` | text | Timing text |
| `duration` | text | Duration/course text |
| `quantity` | text | Quantity/refill text |
| `action` | text | `start`, `continue`, `stop`, `change`, or `unknown` |
| `indication` | text | Reason if stated or user-confirmed |
| `confidence` | real | Manual extraction confidence |
| `needs_review` | integer | `1` if the row needs manual/user review |
| `source_page` | integer | Encounter page order |
| `source_file` | text | Source path |
| `raw_visual_note` | text | Short visual/source note |
| `warnings_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## `prescription_facts`

One row per non-medication fact.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `encounter_id` | text | Foreign key |
| `fact_index` | integer | Sidecar list index |
| `fact_type` | text | `diagnosis`, `symptom`, `vital`, `test_advised`, `lifestyle_advice`, `follow_up`, `referral`, `note`, `doctor_question`, or `other` |
| `label` | text | Fact label |
| `value_text` | text | Preserved fact text |
| `normalized_value` | text | Normalized value when useful |
| `confidence` | real | Manual extraction confidence |
| `needs_review` | integer | `1` if the row needs review |
| `source_page` | integer | Encounter page order |
| `source_file` | text | Source path |
| `raw_visual_note` | text | Short visual/source note |
| `warnings_json` | text | JSON array |
| `imported_at` | text | Import timestamp |

## Reprocessing Behavior

The loader upserts `prescription_encounters` by `encounter_id`, then deletes and reinserts all page, medication, and fact rows for that encounter. Re-importing a corrected sidecar therefore removes stale child rows.

## Example Queries

Rows needing review:

```sql
select e.prescription_date, e.status, m.raw_name, m.dose, m.frequency, m.duration, m.raw_visual_note
from medication_orders m
join prescription_encounters e using (encounter_id)
where e.status in ('needs_review', 'needs_user_review')
   or m.needs_review = 1
order by e.prescription_date, m.order_index;
```

Medication history:

```sql
select e.prescription_date, m.raw_name, m.strength, m.dose, m.frequency, m.duration, m.action, e.prescriber
from medication_orders m
join prescription_encounters e using (encounter_id)
where lower(coalesce(m.normalized_name, m.raw_name)) like '%thyronorm%'
order by e.prescription_date;
```

Advised tests and follow-up:

```sql
select e.prescription_date, f.fact_type, f.label, f.value_text, e.prescriber
from prescription_facts f
join prescription_encounters e using (encounter_id)
where f.fact_type in ('test_advised', 'follow_up')
order by e.prescription_date, f.fact_index;
```

Unresolved user questions:

```sql
select prescription_date, encounter_id, unresolved_questions_json
from prescription_encounters
where status = 'needs_user_review'
   or unresolved_questions_json != '[]'
order by prescription_date;
```
