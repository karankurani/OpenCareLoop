# Multi-Person Medical Workspace

This repository stores longitudinal medical dossiers for multiple people. Keep
shared tooling at the workspace root and keep each person's medical data inside
`people/<person-slug>/`.

## Scope

- This workspace is for non-urgent issues only.
- Do not spend time on generic public-health disclaimers or broad
  government/medical-body boilerplate.
- Build ranked possibilities, evidence, missing data, and next steps.
- If a conversation unexpectedly becomes urgent, say so plainly and stop the
  normal workflow.

## Privacy Rules

- Treat all health information as sensitive.
- Keep personally identifying details only when they help medical care.
- Prefer dates, symptoms, test results, medicine names, dosages, and doctor
  instructions over speculation.
- Do not upload records, prescriptions, lab reports, scans, or IDs to external
  services unless explicitly approved.
- When summarizing records for sharing, remove unnecessary identifiers.

## Layout

Use this structure by default:

```text
root-folder/
  AGENTS.md
  requirements.txt
  skills/
  people/
    <person-slug>/
      AGENTS.md
      raw-data-dump/
      profile.md
      current-concerns.md
      timeline.md
      medications.md
      medication-images/
        raw/
        sidecars/
        medication_images.sqlite
      lifestyle.md
      labs/
        raw/
        sidecars/
        labs.sqlite
      prescriptions/
        raw/
        sidecars/
        prescriptions.sqlite
      imaging/
        raw/
        sidecars/
        imaging.sqlite
      visits/
      symptom-logs/
      summaries/
      questions-for-doctor.md
```

## Working Rules

- Keep shared skills and automations at the workspace root.
- Put person-specific records, SQLite files, and dossier Markdown only inside
  that person's folder.
- Read this root file for common workflow and the relevant
  `people/<person-slug>/AGENTS.md` for case-specific context.
- Default to readable lowercase person slugs.
- Use `.venv/bin/python` for project Python scripts.
- Do not overwrite original medical records.

## Working Style

Future agents should:

- Ask focused questions before giving analysis.
- For an existing person, resume from the current dossier before asking first-intake
  questions again.
- When asking the user to confirm or double-check anything from a record, include clickable local file links to the relevant source files so the user can open them directly.
- Separate facts, assumptions, and questions.
- Use absolute dates whenever possible.
- Preserve units and reference ranges for lab values.
- Track whether a symptom is new, worsening, improving, recurring, or resolved.
- Flag missing information instead of filling gaps with assumptions.
- Explain medical uncertainty plainly.
- For any differential diagnosis, include what would make each possibility more
  or less likely and what information is missing.
- Use medical references when needed for precision, but keep the output
  specific to the active case and avoid generic advice dumps.
- Keep outputs practical: timelines, checklists, appointment notes, and concise
  summaries.

## Returning Person Workflow

When the user is returning to discuss someone who already has a folder under
`people/<person-slug>/`, do a brief resync instead of restarting intake.

1. Identify the person and read the root `AGENTS.md`, the person's
   `AGENTS.md`, and the concise dossier files: `profile.md`,
   `current-concerns.md`, `timeline.md`, `medications.md`, `lifestyle.md`, and
   `questions-for-doctor.md` when present.
2. Check `people/<person-slug>/raw-data-dump/` and relevant sidecars/SQLite
   only if the user mentions new records, recent tests, prescriptions, imaging,
   or visit notes.
3. Start with a compact case status: active concerns, current medications,
   latest dated events, unresolved questions, and obvious stale/missing data.
4. Ask concise follow-up questions in small batches. Prefer questions that
   determine what changed since the last dated dossier entry: new symptoms,
   worsening/improving/resolved symptoms, medication changes, new doctor advice,
   new test results, and what the user wants to decide next.
5. Update the dossier as the conversation produces confirmed facts. Keep
   `current-concerns.md` current, append or revise `timeline.md` for dated
   changes, update `medications.md` for starts/stops/dose changes, and refresh
   `questions-for-doctor.md` when new doctor-facing questions emerge.
6. At the end of a follow-up session, summarize what changed, what remains
   uncertain, and the next small batch of questions or records needed.

Use `skills/dossier-sync` for this resync loop when the update depends on
structured sidecars/SQLite or when multiple dossier files need coordinated
updates. For a simple manual update, edit the relevant dossier files directly
while preserving the same source discipline.

## Change And Action Suggestions

When the user asks what they should change or do:

- Start from the person's current dossier, not generic advice.
- Suggest the smallest reasonable changes first, favoring reversible,
  low-risk steps such as tracking symptoms, clarifying medication timing,
  gathering records, preparing appointment questions, hydration/sleep/activity
  adjustments, or checking home measurements when already available.
- Separate actions into `reasonable now`, `ask the doctor first`, and
  `urgent / do not wait` only when the facts justify those buckets.
- It is appropriate to suggest treatment, medication, supplement, diet, testing,
  or procedure changes as options to discuss with the doctor when they may solve
  the current issue. Explain why the option is being raised and what specific
  question the patient should ask.
- For anything even slightly risky, such as changing prescription dose or
  timing, stopping or starting a medicine or supplement, combining medicines,
  fasting, intense exercise, pregnancy-related decisions, procedures, or
  delaying care, keep it in the `ask the doctor first` bucket and say plainly
  that they should not make the change before checking with their doctor.
- Do not present medication, supplement, diet, or treatment changes as direct
  orders. Phrase risk-bearing changes as doctor-discussion options, with the
  reason, expected benefit, and main safety concern.
- Include what would make each suggestion inappropriate or a reason to stop and
  ask for medical help.

## Shared Skills And Storage Rules

- Use `skills/lab-data-ingest` for lab report ingestion.
- Use `skills/prescription-data-ingest` for prescription ingestion.
- Use `skills/medication-image-ingest` for medicine package, blister-strip,
  bottle, vial, sticker, and label-image ingestion.
- Use `skills/imaging-data-ingest` for imaging, radiology, and procedure
  report ingestion.
- Use `skills/dossier-sync` before updating dossier Markdown from structured
  ingest output.
- Use `skills/dossier-sync` for returning-person resync when follow-up answers
  or new records affect multiple dossier files.
- `skills/dossier-sync` is optional for ordinary manual dossier updates; the
  dossier may also be updated directly in separate intake, analysis, or
  follow-up sessions.
- New records should enter through `people/<person-slug>/raw-data-dump/`.
- Sort raw files into the matching person-local subfolders before structured
  ingestion.
- Put original lab PDFs/text/spreadsheets in `people/<person-slug>/labs/raw/`
  after sorting.
- Write extracted JSON sidecars to `people/<person-slug>/labs/sidecars/`.
- Store the lab SQLite database at `people/<person-slug>/labs/labs.sqlite`.
- Put original prescription images/PDFs in
  `people/<person-slug>/prescriptions/raw/<encounter-id>/` after sorting.
- Write prescription JSON sidecars to
  `people/<person-slug>/prescriptions/sidecars/`.
- Store the prescription SQLite database at
  `people/<person-slug>/prescriptions/prescriptions.sqlite`.
- Put original medicine-product images/PDFs in
  `people/<person-slug>/medication-images/raw/<capture-id>/` after sorting.
- Write medication-image JSON sidecars to
  `people/<person-slug>/medication-images/sidecars/`.
- Store the medication-image SQLite database at
  `people/<person-slug>/medication-images/medication_images.sqlite`.
- Put original imaging/procedure images/PDFs in
  `people/<person-slug>/imaging/raw/<study-id>/` after sorting.
- Write imaging/procedure JSON sidecars to
  `people/<person-slug>/imaging/sidecars/`.
- Store the imaging SQLite database at
  `people/<person-slug>/imaging/imaging.sqlite`.
- Keep generated sidecars and SQLite indexes separate from raw files.

## Raw Data Intake

- Always ingest new external files from `people/<person-slug>/raw-data-dump/`
  first.
- Classify each file by type: lab, imaging/procedure, visit note, prescription,
  medication image, symptom log, or miscellaneous.
- Process raw intake in small batches. Prefer one encounter, report, study,
  medication capture, or tightly related file group at a time; for large dumps,
  pause after each batch to summarize what was classified, what moved, what was
  ingested, and what remains.
- Do not bury ambiguous files inside a large batch. When identity, date, file
  type, encounter grouping, duplicate status, current-vs-past status, source
  readability, or clinical meaning is unclear, stop and ask a focused question
  before finalizing sidecars, SQLite imports, or dossier updates.
- Move each file into its appropriate folder before running specialized
  extraction.
- Preserve original filenames when useful; otherwise rename with an ISO date
  prefix when the document date is known.
- Keep generated structured data separate from raw files.
- For each batch, leave a concise review note in the conversation: files handled,
  source destinations, generated sidecars/SQLite imports, uncertainties kept in
  review, and the next proposed batch.

## Intake Workflow

Use this sequence for any person:

1. Establish basic profile.
2. Capture the chief concerns in the person's own words.
3. Build a symptom timeline.
4. Collect current and past medications, supplements, and allergies.
5. Gather known diagnoses, surgeries, hospitalizations, pregnancies, and major
   illnesses when relevant.
6. Add labs, imaging, prescriptions, and visit notes with dates.
7. Identify patterns and missing data.
8. Draft questions and options.
9. Later, when enough data exists, build ranked diagnostic hypotheses.
10. Update the timeline after each new visit, test, or treatment change.

## First Questions

Start with these questions. Ask in small batches so the answers stay accurate.

### Basic Profile

1. Age and date of birth?
2. Height and current weight?
3. City/country, and whether they have access to a primary doctor or specialist?
4. Main languages preferred for medical notes?

### Current Concerns

For each current issue:

1. What symptom or problem is happening?
2. When did it start? Use the exact date if possible.
3. Was onset sudden or gradual?
4. Is it constant or intermittent?
5. What makes it better or worse?
6. Severity from `0` to `10`?
7. Any associated symptoms?
8. Has this happened before?
9. What has already been tried, and did it help?
10. What do they think may be connected to it?

### Medical Background

1. Known diagnoses, with approximate dates?
2. Surgeries or hospitalizations, with dates and reasons?
3. Current medicines: name, dose, frequency, start date, reason, prescribing
   doctor.
4. Supplements, Ayurvedic/homeopathic remedies, OTC medicines, and painkillers.
5. Allergies or bad reactions to medicines, foods, contrast dye, latex, or
   vaccines.
6. Recent infections, injuries, travel, major stress, sleep disruption, or
   weight change.

### Reproductive And Hormonal History

Ask only when relevant and with privacy in mind:

1. Menstrual cycle pattern, last menstrual period, and any recent changes?
2. Pregnancy history, miscarriages, deliveries, complications, or fertility
   treatments?
3. Contraception or hormone therapy?
4. Symptoms around periods: pain, heavy bleeding, mood changes, migraines,
   fainting, bowel changes.

### Family And Lifestyle

1. Family history of diabetes, thyroid disease, hypertension, heart disease,
   stroke, cancer, autoimmune disease, clotting disorders, mental health
   conditions, or early sudden death?
2. Diet pattern, appetite, hydration, caffeine, alcohol, tobacco, recreational
   drugs.
3. Sleep schedule and sleep quality.
4. Physical activity and limitations.
5. Work pattern, caregiving load, environmental exposures, and major stressors.

### Records To Gather

Ask for available records and capture dates:

- Recent prescriptions.
- Photos of current medicines, blister packs, bottles, boxes, pharmacy labels,
  or stickers when available.
- Lab reports with reference ranges.
- Imaging reports, not just images.
- Hospital discharge summaries.
- Doctor visit notes.
- Vaccination records.
- Home measurements: blood pressure, pulse, temperature, glucose, weight,
  oxygen saturation, menstrual tracking, symptom logs.

## Data Capture Format

When adding a new medical event, use:

```text
Date:
Event type: symptom | visit | lab | imaging | medication | procedure | diagnosis | note
Summary:
Details:
Source:
Open questions:
Follow-up needed:
```

When adding a medication, use:

```text
Name:
Dose:
Frequency:
Route:
Start date:
Stop date:
Reason:
Prescriber:
Effect:
Side effects:
Notes:
```

When adding a lab, use:

```text
Date:
Test:
Result:
Unit:
Reference range:
Flag: low | normal | high | critical | unknown
Lab name:
Context:
```

## Default Deliverables

After the initial intake, create these files under `people/<person-slug>/`:

1. `profile.md` with stable background details.
2. `current-concerns.md` with active symptoms and priorities.
3. `timeline.md` with dated events.
4. `questions-for-doctor.md` with the top appointment questions.

Keep these concise and easy to update.
