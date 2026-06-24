---
title: Add your records
sidebar_label: Add your records
description: Where to put records so the agent can read them.
---

# Add your records

Add a record whenever it can pin down a date, a result, a medicine, a diagnosis, doctor advice, or what happened at a visit.

Records that help:

- Lab reports with units and reference ranges.
- Prescriptions and pharmacy labels.
- Photos of medicine boxes, strips, bottles, vials, or stickers.
- Imaging and procedure reports.
- Doctor visit notes.
- Hospital discharge summaries.
- Vaccination records.
- Symptom logs.
- Home measurements.

## Where files go

Drop new files for a person into their intake folder:

```text
people/<person-slug>/raw-data-dump/
```

The `<person-slug>` is just that person's folder name, like `karan`. Then tell the agent what you added:

```text
I added Karan's blood test report from 2026-06-12 to his raw-data-dump. Please classify it and update the dossier after review.
```

The agent works through documents in small batches, reads each one carefully, and asks whenever something is unclear. Your original files are never overwritten — it keeps them and builds its notes alongside.
