# OpenCareLoop

OpenCareLoop is an AI agent loop that helps you manage your family's health over a period of time. And start fixing issues which human doctors frequently do not have time for. It has the medical intelligence of frontier models combined with the patience of an AI vs a human doctor who has limited time.

The time investment needed by users is high. It only gets effective after giving proper inputs over multiple sessions where each session is multiple hours long. The information given to this agent must be truthful, factual based and as unambiguous as possible. Facts, not feelings.

It is meant to be for non-urgent uses only.

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Important Warnings

> [!WARNING]
> OpenCareLoop is not a medical device, clinician, emergency service, diagnosis
> engine, or treatment system. It does not replace a doctor, pharmacist, nurse,
> qualified clinician, emergency department, poison-control service, or local
> urgent-care pathway.
> Do not use this project for urgent or emergency situations. If a situation may
> be urgent, stop using the normal workflow and seek appropriate medical help.
> Do not use generated summaries, extracted record data, ranked possibilities,
> or appointment questions as medical orders. Medication changes, dose changes,
> stopping or starting medicines or supplements, procedure decisions, fasting,
> pregnancy-related decisions, delaying care, or other risk-bearing changes
> should be checked with a qualified clinician first.
> Medical records can be incomplete, ambiguous, outdated, misread,
> mistranscribed, or incorrectly linked to the wrong person. Treat all extracted
> data and dossier summaries as review material until checked against the
> original record and, when needed, confirmed by the patient or clinician.
> This repository may contain sensitive health information. Do not publish,
> commit, upload, share, or send personal medical records, prescriptions, lab
> reports, scans, IDs, or dossier files unless the affected person has approved
> that disclosure and you understand the privacy consequences.
> OpenCareLoop does not by itself provide HIPAA, GDPR, clinical-safety,
> security, audit, consent-management, or regulatory compliance. Anyone using or
> modifying it is responsible for the laws, policies, and safeguards that apply
> to their setting.

## Getting Started

### 1. Open this folder with an AI agent

Open this repository folder in Codex or an equivalent AI coding-agent
environment that can read and write local files.

> [!IMPORTANT]
> This works with frontier models - GPT 5.5/equivalent and above.

Start by telling the agent the person's name and that you want to create or
continue their OpenCareLoop dossier.

Example:

```text
This is for Maria. Lets start a new dossier for her.
```

The agent will create a readable person slug, set up the
person folder, and begin the intake in small batches.

### 2. Answer the first intake questions

You can then start asking the agent to ask focused questions about the person, current concerns,
medications, medical history, lifestyle, and available records. Answer only what
you know. It is fine to say that a date, dose, diagnosis, or record is missing.

The agent will create and maintain the first dossier files for you.

### 3. Add records when the agent asks

When you have lab reports, prescriptions, medicine photos, imaging reports,
visit notes, or symptom logs, place them in:

```text
people/<person-slug>/raw-data-dump/
```

Then tell the agent what you added. The agent will classify the files and handle its ingestion. It will ask clarifications etc as part of the loop.

### 4. The Care Loop

The loop is where it gets effective - you have to keep on giving more information about the person, their lifestyle, their family history etc. A single session rarely covers it. Revisit this and keep on asking the agent to ask your questions. And then ask it to suggest changes for long standing issues.

For example - If the person has chronic pain, make that a current concern and keep on giving it information and ask for changes to test to help with it.

This agent is not magic, it will not fix things that are proven to not be fixable but it will give you directions to explore. It will help you understand the underlying mechanics and the long term picture.

The long term picture is where the value is - our health is accumulation of our life and its lifestyle and its genes. Combining that in a single place with an infintely patient intelligence will yeild results.

Example - one person had chronic issues of pain in their legs. The visits to doctors and orthopaedics got written off as an age related symptom. But the pain relief mechanics given by the doctors were not effective. After observing the person's dossier for two weeks and ingesting over decade worth of history - the agent suggested one behaviour change which fixed the pain. It was an age related issue, but figuring out when it triggers and then how to avoid it was where the doctors did not have time for but an AI does.

The more this loop is done - ideally over months and years - the more it will have a chance of giving a valuable insight.
