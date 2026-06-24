---
title: Work with the agent
sidebar_label: Work with the agent
description: Prompts that work, how to answer well, and why accuracy matters.
---

# Work with the agent

OpenCareLoop is at its best when you ask for specific, practical work: organize the facts, find what's missing, update the timeline, suggest one change, prepare questions.

## Prompts that work

Start a new dossier:

```text
This is for Karan. Let's start a new OpenCareLoop dossier for him.
```

Resume one:

```text
This is for Karan. Please read his current dossier, summarize the status, and ask what changed.
```

Report a change:

```text
Karan's knee pain improved from 7/10 to 3/10 after reducing stair climbing for two weeks. Please update the current concern and timeline.
```

Prepare for an appointment:

```text
Please turn Karan's current dossier into a concise appointment note and the top questions for his doctor.
```

Ask for possible explanations:

```text
Based on the dossier, build ranked possibilities for the fatigue. Separate facts, assumptions, missing data, and next questions.
```

## How to answer well

When the agent asks you something, the most useful answers include:

- Dates, even approximate ones.
- Symptom severity from 0 to 10.
- Whether a symptom is new, worsening, improving, recurring, or resolved.
- Medicine names, doses, timing, start dates, and reasons.
- What helped, what didn't, and what caused side effects.
- Where the information came from — memory, doctor advice, a prescription, a lab report, or a home measurement.

Short, factual answers beat long, uncertain stories. If you're not sure, say what's uncertain.

## Be accurate

Accuracy matters more than polish. A short note with real dates and honest uncertainty is worth far more than a confident but vague summary.

Use exact dates when you have them:

```text
Started metformin on 2026-05-03.
```

And when you don't, say so plainly:

```text
Started sometime in early May 2026. Exact date unknown.
```

The agent would rather record "unknown" than guess.
