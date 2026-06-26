#!/usr/bin/env python3
"""Update OpenCareLoop tooling in place without touching personal data.

Replaces the small, fixed set of shipped tooling files (root docs + skills/)
and prunes stale skill files, while never reading, writing, or deleting
anything under people/, .venv/, raw-data-dump/, or any other non-tooling path.

Stdlib only, so it runs before the virtual environment is rebuilt.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

# This script lives at <ROOT>/skills/opencareloop-update/scripts/<this file>.
SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[1]
PACKAGE_ROOT = "OpenCareLoop"
DEFAULT_REPO = "karankurani/OpenCareLoop"
DEFAULT_ASSET = "OpenCareLoop.zip"

# The release manifest ships next to this script and is the single source of
# truth for the tooling surface (shared with scripts/build_release_zip.py).
sys.path.insert(0, str(SKILL_DIR))
try:
    from release_manifest import (  # type: ignore[import]
        FORBIDDEN_PARTS,
        SKILL_FILE_SUFFIXES,
        ROOT_FILES as _MANIFEST_ROOT_FILES,
    )
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"Missing release_manifest.py next to the updater: {exc}")

# VERSION is injected at zip-build time, so it is not in the manifest list but
# is a valid tooling file to replace.
ROOT_FILES = frozenset(_MANIFEST_ROOT_FILES) | {"VERSION"}
REQUIRED_PACKAGE_FILES = frozenset({
    "skills/opencareloop-update/SKILL.md",
    "skills/opencareloop-update/release_manifest.py",
    "skills/opencareloop-update/scripts/update_opencareloop.py",
})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update OpenCareLoop tooling in place.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing anything.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Apply the latest release even if the local VERSION already matches.",
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub owner/repo.")
    parser.add_argument("--asset", default=DEFAULT_ASSET, help="Release asset filename.")
    parser.add_argument(
        "--zip",
        dest="zip_path",
        default=None,
        help="Use a local release zip instead of downloading (for testing).",
    )
    return parser.parse_args()


def local_version() -> str | None:
    path = ROOT / "VERSION"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip() or None
    return None


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": "opencareloop-update",
            "Accept": "application/vnd.github+json",
        },
    )


def latest_release(repo: str, asset: str) -> tuple[str, str]:
    """Return (tag, asset_download_url) for the newest non-draft release.

    Uses the releases list rather than /releases/latest because OpenCareLoop
    publishes prereleases, which /latest skips.
    """
    url = f"https://api.github.com/repos/{repo}/releases?per_page=10"
    try:
        with urllib.request.urlopen(_request(url), timeout=30) as resp:
            releases = json.load(resp)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
        raise SystemExit(f"GitHub API error {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise SystemExit(f"Could not reach GitHub: {exc.reason}")

    for release in releases:
        if release.get("draft"):
            continue
        for item in release.get("assets", []):
            if item.get("name") == asset:
                return release.get("tag_name"), item["browser_download_url"]
    raise SystemExit(f"No release asset named {asset!r} found for {repo}.")


def download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(_request(url), timeout=120) as resp, dest.open("wb") as fh:
        shutil.copyfileobj(resp, fh)


def find_package_dir(extract_dir: Path) -> Path:
    candidate = extract_dir / PACKAGE_ROOT
    if (candidate / "AGENTS.md").is_file():
        return candidate
    # Fall back to a single top-level directory if the layout shifts.
    dirs = [p for p in extract_dir.iterdir() if p.is_dir()]
    if len(dirs) == 1 and (dirs[0] / "AGENTS.md").is_file():
        return dirs[0]
    raise SystemExit("Unexpected release archive layout: AGENTS.md not found.")


def assert_safe_target(target: Path) -> None:
    rel = target.resolve().relative_to(ROOT)
    parts = rel.parts
    if set(parts) & FORBIDDEN_PARTS:
        raise SystemExit(f"Refusing to touch protected path: {rel}")
    if parts[0] == "skills" or (len(parts) == 1 and parts[0] in ROOT_FILES):
        return
    raise SystemExit(f"Refusing to touch non-tooling path: {rel}")


def skill_files(base: Path) -> set[str]:
    """Relative posix paths of shippable skill files under base/skills."""
    skills_dir = base / "skills"
    if not skills_dir.is_dir():
        return set()
    return {
        p.relative_to(base).as_posix()
        for p in skills_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SKILL_FILE_SUFFIXES
    }


def package_tooling_files(pkg: Path) -> set[str]:
    """Every tooling file shipped in the extracted package."""
    root = {name for name in ROOT_FILES if (pkg / name).is_file()}
    return root | skill_files(pkg)


def validate_package_files(files: set[str]) -> None:
    missing = sorted(REQUIRED_PACKAGE_FILES - files)
    if missing:
        formatted = "\n".join(f"  - {rel}" for rel in missing)
        raise SystemExit(
            "Release package is missing required updater files:\n"
            f"{formatted}\n"
            "Refusing to update because pruning could remove local tooling."
        )


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def prune_empty_skill_dirs() -> None:
    for path in sorted((ROOT / "skills").rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def print_plan(added: list[str], changed: list[str], removed: list[str]) -> None:
    for label, mark, items in (
        ("Added", "+", added),
        ("Updated", "~", changed),
        ("Removed", "-", removed),
    ):
        print(f"{label}: {len(items)}")
        for rel in items:
            print(f"  {mark} {rel}")


def resolve_source(args: argparse.Namespace) -> tuple[str, str | None, Path | None]:
    """Return (tag, download_url, local_zip) for the chosen update source."""
    if args.zip_path:
        zip_path = Path(args.zip_path).resolve()
        if not zip_path.is_file():
            raise SystemExit(f"Local zip not found: {zip_path}")
        return "(local zip)", None, zip_path
    tag, url = latest_release(args.repo, args.asset)
    return tag, url, None


def main() -> int:
    args = parse_args()

    have = local_version()
    latest_tag, download_url, zip_path = resolve_source(args)
    print(f"Local version:  {have or '(unknown)'}")
    print(f"Latest version: {latest_tag}")

    if have == latest_tag and not args.force and not args.zip_path:
        print("Already up to date. Use --force to reapply.")
        return 0

    work = Path(tempfile.mkdtemp(prefix="opencareloop-update-"))
    try:
        if download_url:
            zip_path = work / args.asset
            print(f"Downloading {latest_tag} ...")
            download(download_url, zip_path)

        extract_dir = work / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        pkg = find_package_dir(extract_dir)

        new_files = package_tooling_files(pkg)
        if not new_files:
            raise SystemExit("Release package contained no tooling files.")
        validate_package_files(new_files)

        # Plan: classify each target before touching the filesystem.
        new_skills = {f for f in new_files if f.startswith("skills/")}
        removed = sorted(skill_files(ROOT) - new_skills)
        added, changed = [], []
        for rel in sorted(new_files):
            dst = ROOT / rel
            if not dst.exists():
                added.append(rel)
            elif dst.read_bytes() != (pkg / rel).read_bytes():
                changed.append(rel)

        for rel in (*added, *changed, *removed):
            assert_safe_target(ROOT / rel)

        if args.dry_run:
            print("\n-- dry run (no changes written) --")
        print_plan(added, changed, removed)

        if args.dry_run:
            print("\nRe-run without --dry-run to apply.")
            return 0
        if not (added or changed or removed):
            print("\nAlready matches the latest release; nothing to change.")
            return 0

        # Apply: back up anything being overwritten or removed, then write.
        backup = Path(tempfile.mkdtemp(prefix="opencareloop-backup-"))
        print(f"\nBackup of replaced files: {backup}")
        for rel in changed + removed:
            copy(ROOT / rel, backup / rel)
        for rel in added + changed:
            copy(pkg / rel, ROOT / rel)
        for rel in removed:
            (ROOT / rel).unlink()
        prune_empty_skill_dirs()

        if "requirements.txt" in added + changed:
            print(
                "\nrequirements.txt changed. Rebuild the environment:\n"
                "  .venv/bin/python -m pip install -r requirements.txt"
            )
        print(f"\nUpdated OpenCareLoop to {latest_tag}.")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
