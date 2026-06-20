---
name: dossier-sync
description: Use after structured medical ingest, reprocessing, or a returning-person follow-up conversation when Codex needs to update a person's human-readable dossier Markdown from confirmed user updates, lab, prescription, visit, imaging, symptom-log, or other sidecar/SQLite evidence without duplicating, overwriting, or promoting uncertain data.
---

# Dossier Sync

Use this skill after an ingest skill has produced or reprocessed structured evidence,
or when a returning user gives follow-up updates that should change the dossier.
The goal is a concise, longitudinal clinical dossier backed by raw records,
sidecars, and confirmed user statements, not a full dump of every extracted row.
Run it against the active person's folder, typically `people/<person-slug>/`.

## Source Order

Treat sources in this order:

1. Original raw records are immutable evidence.
2. Sidecars hold extracted facts, uncertainty, source paths, hashes, review status, and user confirmations.
3. SQLite databases are searchable indexes of sidecars.
4. Dossier Markdown is the concise human-readable clinical summary.

Do not make the dossier more confident than the sidecar. If a fact is ambiguous, cropped, future/separate, contradicted, or marked `needs_review` / `needs_user_review`, keep it in the sidecar or SQLite review queue unless the dossier explicitly needs a marked open question.

## Pre-Sync Checks

Before editing any dossier file:

- Read `git status --short`.
- Read the current target file contents.
- Read relevant diffs for the files you will touch.
- Identify whether existing uncommitted edits may be from the user or another agent; preserve them.
- If a target file already contains related information, update the existing entry narrowly instead of adding a duplicate.

Never regenerate whole dossier files from sidecars. Make minimal, additive edits.

## Returning-Person Resync Loop

Use this loop when the person already has dossier files and the user is continuing
care, asking what changed, asking what to do next, or reporting a new symptom,
visit, prescription, test, or treatment response.

1. Read the person's `AGENTS.md` and the concise dossier files that exist:
   `profile.md`, `current-concerns.md`, `timeline.md`, `medications.md`,
   `lifestyle.md`, and `questions-for-doctor.md`.
2. Identify the latest dated timeline entry and any active concerns,
   medications, unresolved doctor questions, or missing facts.
3. If the user mentions new records, check `raw-data-dump/` and the matching
   sidecars/SQLite. Do not upload records externally.
4. Ask only the next small batch of questions needed to update the dossier:
   what changed, exact dates, severity/status, medication or dose changes,
   doctor instructions, tests done, and whether symptoms are new, worsening,
   improving, recurring, or resolved.
5. Update dossier Markdown only with confirmed facts from the conversation or
   clear source evidence. Keep uncertain items as open questions.
6. End with a concise resync summary: files changed, active concerns now,
   unresolved questions, and the next practical step or record needed.

Do not ask the full first-intake question set again unless the dossier is empty
or the missing background is directly relevant to the current issue.

## What Can Sync

Sync confirmed facts by default:

- Facts visible in the source and clear in the sidecar.
- Facts explicitly confirmed by the user.
- Corrected facts from reprocessing when the sidecar records the correction in `user_confirmations` or `reprocess_reason`.

Do not sync by default:

- Possible medication names, unclear doses, unclear frequency, or unclear current-vs-past status.
- Lab values missing units, dates, patient identity, or reference context.
- Future/separate tests or instructions that the user says should not affect current analysis.
- Raw extraction questions that are not doctor-facing.
- Inferred diagnoses or indications unless the source or user explicitly states them.

If the dossier must mention an uncertain item, label it plainly as uncertain and keep the uncertainty source-specific.

## File Routing

- `profile.md`: stable demographics, long-term background, access to care, languages, major history.
- `current-concerns.md`: active symptoms, priorities, recent changes, current symptom context.
- `timeline.md`: dated symptoms, visits, diagnoses, procedures, medication starts/stops/changes, major lab/imaging results, and treatment responses.
- `medications.md`: active medicines/supplements, recently completed courses, past medicines, medication questions, adverse effects.
- `lifestyle.md`: stable diet, sleep, activity, work/caregiving load, exposures,
  and changes that may affect symptoms or treatment decisions.
- `visits/*.md`: encounter-specific reason, vitals, exam/impression if stated, orders, instructions, follow-up, source notes.
- `questions-for-doctor.md`: only questions intended for the doctor, not raw transcription uncertainties.
- `summaries/*.md`: appointment-ready summaries; update only when requested or when the summary is explicitly being refreshed.

Keep detailed row-level labs in `people/<person-slug>/labs/sidecars/` and `people/<person-slug>/labs/labs.sqlite`. Keep prescription order details and unresolved prescription transcription questions in `people/<person-slug>/prescriptions/sidecars/` and `people/<person-slug>/prescriptions/prescriptions.sqlite`.

## Conflict Rules

- If sidecar evidence conflicts with dossier text, do not silently replace the dossier.
- Prefer the newer sidecar only when it is clearly user-confirmed or a documented reprocess correction.
- Otherwise add or retain an open question and ask the user for confirmation.
- If a user statement conflicts with a record, preserve both until clarified:
  label the user statement as reported and link or cite the source record when
  asking for confirmation.
- Preserve absolute dates, doses, frequencies, units, reference ranges, and source context.
- Do not delete another agent's or user's notes unless explicitly confirmed as wrong.

## Action Suggestions

When the resync ends with "what should I change or do?" or a similar request:

- Ground suggestions in the current dossier and the newest confirmed update.
- Prefer minimal, low-risk, reversible changes first.
- Suggest treatment, medication, supplement, diet, testing, or procedure changes
  as doctor-discussion options when they may solve the current issue. For each
  option, explain why it is being raised and give the exact question to ask the
  doctor.
- Put prescription changes, stopping/starting supplements, dose timing changes,
  combining medicines, intense exercise, fasting, pregnancy-related decisions,
  procedures, or delaying care in an "ask the doctor first" bucket unless a
  doctor has already instructed that exact change. Make clear that the patient
  should not make those changes before checking with the doctor.
- Include what would make a suggestion unsafe or a reason to seek timely care.
- Avoid generic boilerplate; make the safety note specific to the proposed
  change and the person's known context.

## Reprocessing

When a report or prescription is reprocessed:

- Preserve the existing report or encounter ID.
- Update the sidecar's reprocessing fields according to that ingest skill.
- Re-import SQLite so stale child rows are replaced.
- Update dossier Markdown only if the corrected fact changes current medications, past medications, timeline events, active concerns, visit summaries, or doctor-facing questions.
- Avoid duplicate timeline rows; revise the existing row if it describes the same event.

## Final Sync Check

Before finishing:

- Validate any edited sidecar JSON or SQLite import through the ingest skill if applicable.
- Re-read the changed dossier snippets.
- Run a small query or search when useful to confirm uncertain rows stayed in review queues.
- Report what was synced, what stayed review-only, and any remaining user-confirmation questions.
