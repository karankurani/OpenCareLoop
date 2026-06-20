# SQLite Schema

The ingestion script creates this database if missing.

The script opens SQLite with WAL mode, `busy_timeout = 5000`, `synchronous = normal`, and `foreign_keys = on` so analytics queries can read while ingestion writes.

## `reports`

One row per ingested source file.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `source_path` | text unique | Path provided to the ingest script |
| `source_sha256` | text | Source file hash |
| `sidecar_path` | text | JSON sidecar path |
| `patient_name` | text | Extracted if available |
| `report_date` | text | Normalized `YYYY-MM-DD` when possible |
| `report_date_text` | text | Raw date text from report |
| `ingested_at` | text | UTC timestamp |
| `parser_version` | text | Extractor version |
| `status` | text | `ok`, `needs_review`, or `no_text` |
| `warnings_json` | text | JSON array of warning strings |

## `lab_results`

One row per extracted candidate lab result.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer primary key | Internal row id |
| `report_id` | integer | Foreign key to `reports.id` |
| `test_name` | text | Test name from report |
| `normalized_test_name` | text | Lowercase normalized name for matching |
| `value_text` | text | Original value text |
| `value_numeric` | real | Parsed numeric value when available |
| `unit` | text | Unit from report |
| `reference_range` | text | Reference interval text |
| `flag` | text | `low`, `normal`, `high`, `critical`, `abnormal`, or `unknown` |
| `specimen` | text | Usually blank unless extracted |
| `category` | text | Optional grouping such as thyroid/lipid/metabolic |
| `page` | integer | PDF page when known |
| `line_number` | integer | Source text line number |
| `confidence` | real | Parser confidence, `0` to `1` |
| `needs_review` | integer | `1` if row should be manually checked |
| `raw_line` | text | Source line used for extraction |
| `created_at` | text | UTC timestamp |

## Example Queries

HbA1c trend:

```sql
select report_date, test_name, value_numeric, unit, reference_range, flag, source_path
from lab_results
join reports on reports.id = lab_results.report_id
where normalized_test_name like '%hba1c%'
   or normalized_test_name like '%glycated hemoglobin%'
order by report_date;
```

Lipid panel:

```sql
select report_date, test_name, value_numeric, unit, reference_range, flag
from lab_results
join reports on reports.id = lab_results.report_id
where category = 'lipid'
order by report_date, test_name;
```

Rows needing review:

```sql
select report_date, test_name, value_text, unit, reference_range, raw_line, source_path
from lab_results
join reports on reports.id = lab_results.report_id
where needs_review = 1
order by report_date, test_name;
```
