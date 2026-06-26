# First-Time Setup

Use these steps when an agent starts work in this workspace.

## Python Environment

Check whether the project virtual environment exists:

```sh
test -x .venv/bin/python
```

If it is missing, create it from the workspace root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Use `.venv/bin/python` for project scripts after setup.

## Person Slug Check

Before beginning the user's requested work, list existing person folders:

```sh
find people -mindepth 1 -maxdepth 1 -type d -print
```

If `people/` does not exist or contains no person folders, say that no existing
person dossiers were found and ask whether to create a new lowercase person
slug. Do not inspect raw medical records during this slug check.

If person folders exist, identify likely relevant slugs from the user's request.
For an existing person, read that person's `AGENTS.md` and concise dossier files
before analysis or updates.

## Updating OpenCareLoop

The installed version is recorded in the root `VERSION` file. To update the
tooling (root docs and `skills/`) to the latest published release without
touching any `people/` data, use `skills/opencareloop-update`:

```sh
# Preview what would change
python3 skills/opencareloop-update/scripts/update_opencareloop.py --dry-run

# Apply
python3 skills/opencareloop-update/scripts/update_opencareloop.py
```

If `requirements.txt` changed, rebuild the environment with
`.venv/bin/python -m pip install -r requirements.txt`.

