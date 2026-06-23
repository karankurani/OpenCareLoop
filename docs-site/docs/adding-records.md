---
title: Adding Records
description: How users should add records to OpenCareLoop.
---

# Adding Records

Add records when they can clarify dates, results, medicines, diagnoses, doctor advice, or what happened during a visit.

Useful records include:

- Lab reports with units and reference ranges.
- Prescriptions and pharmacy labels.
- Photos of medicine boxes, strips, bottles, vials, or stickers.
- Imaging and procedure reports.
- Doctor visit notes.
- Hospital discharge summaries.
- Vaccination records.
- Symptom logs.
- Home measurements.

## Where to put new files

Place new files for a person in:

```text
people/<person-slug>/raw-data-dump/
```

Then tell the agent what you added:

```text
I added Karan's blood test report from 2026-06-12 to his raw-data-dump. Please classify it and update the dossier after review.
```

The agent will go through the documents in small batches and ask clarifying questions.
