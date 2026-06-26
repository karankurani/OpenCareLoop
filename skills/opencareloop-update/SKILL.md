---
name: opencareloop-update
description: Update the OpenCareLoop workspace tooling (root docs and skills/) in place to the latest published release without touching any personal medical data. Use when the user asks to update, upgrade, or get the latest version of OpenCareLoop, refresh the skills, check whether a newer version exists, or apply a new release while preserving everything under people/.
---

# OpenCareLoop Update

## What This Does

Replaces only the shipped tooling surface — the root files
(`README.md`, `START_HERE.md`, `AGENTS.md`, `CLAUDE.md`, `SETUP.md`, `LICENSE`,
`requirements.txt`, `VERSION`) and everything under `skills/` — with the latest
published release, and prunes skill files that no longer ship.

It never reads, writes, or deletes anything under `people/`, `.venv/`,
`raw-data-dump/`, `.git/`, or any other non-tooling path. The script hard-refuses
any target outside the allowlist, so a person's dossiers and records are
untouched.

## When To Use

- The user asks to update / upgrade OpenCareLoop or get the latest skills.
- The user wants to know whether their workspace is on the latest version.
- A release note or the docs mention a new version.

## How To Run

Use the workspace virtual environment is **not** required — the script is stdlib
only and runs even before `.venv` is set up.

1. Show the user what would change first (no writes):

   ```sh
   python3 skills/opencareloop-update/scripts/update_opencareloop.py --dry-run
   ```

2. The script prints the local version, the latest published version, and the
   added / updated / removed file lists. Relay this to the user and confirm
   before applying.

3. Apply the update:

   ```sh
   python3 skills/opencareloop-update/scripts/update_opencareloop.py
   ```

4. If the output says `requirements.txt changed`, rebuild the environment:

   ```sh
   .venv/bin/python -m pip install -r requirements.txt
   ```

## Flags

- `--dry-run` — preview changes without writing.
- `--force` — reapply the latest release even if `VERSION` already matches.
- `--repo OWNER/REPO` — override the source repository (default
  `karankurani/OpenCareLoop`).
- `--asset NAME` — override the release asset filename (default
  `OpenCareLoop.zip`).
- `--zip PATH` — install from a local release zip instead of downloading
  (useful for testing).

## Safety Notes

- Every replaced or removed file is copied into a temporary backup directory
  before the change; the path is printed at the end so a bad update can be
  reverted.
- The version check uses the GitHub releases list (not `/releases/latest`)
  because OpenCareLoop ships prereleases.
- The allowlist in this script mirrors `scripts/build_release_zip.py`. If the
  release file set changes, update both.
- This skill only updates tooling. It does not modify, migrate, or re-ingest any
  dossier data.
