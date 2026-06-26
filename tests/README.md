# Tests

Developer tests for the workspace tooling. These are **not** shipped in release
zips — the release builder only collects root docs listed in
`release_manifest.ROOT_FILES` plus source files under `skills/`, and `tests/`
is neither. Keep tests here (top-level), never inside `skills/`, or they would
leak into releases.

## Running

```sh
.venv/bin/python -m pip install -r requirements-dev.txt   # first time
.venv/bin/python -m pytest                                # all tests
.venv/bin/python -m pytest tests/test_ingest_labs.py -v   # one file
```

## Layout

- `_loader.py` — loads the standalone skill scripts (which are CLIs, not an
  installed package) by file path so tests can call their functions directly.
- `conftest.py` — puts the repo root on `sys.path`.
- `test_ingest_labs.py` — **exemplar** suite. The other `ingest_*.py` scripts
  share its shape (pure normalizers → row dataclass → SQLite writer); copy this
  pattern when giving them full coverage.
- `test_ingest_smoke.py` — cheap import/entrypoint check for every ingest
  script, so untested scripts don't silently break.
- `test_release_safety.py` — pins the privacy invariant that `people/` data,
  the venv, and binary/sensitive files never enter a release zip.

## What does *not* belong here

No real medical data and no `people/` fixtures. Tests build their own data in
`tmp_path`. This keeps the test suite safe to commit and share.
