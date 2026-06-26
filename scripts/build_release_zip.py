#!/usr/bin/env python3
"""Build the downloadable OpenCareLoop starter workspace zip."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "opencareloop-update"))
from release_manifest import BLOCKED_SUFFIXES, FORBIDDEN_PARTS, ROOT_FILES, SKILL_FILE_SUFFIXES  # noqa: E402
DIST = ROOT / "dist"
PACKAGE_ROOT = "OpenCareLoop"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "version",
        nargs="?",
        default=os.environ.get("GITHUB_REF_NAME", "dev"),
        help="Release tag or version string, for example v0.1.0.",
    )
    return parser.parse_args()


def normalized_version(version: str) -> str:
    clean = version.strip()
    if not clean:
        raise SystemExit("Version must not be empty.")
    return clean


def iter_release_files() -> list[Path]:
    files: list[Path] = []

    for rel in ROOT_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Required release file missing: {rel}")
        files.append(path)

    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        raise SystemExit("Required directory missing: skills")

    for path in sorted(skills_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SKILL_FILE_SUFFIXES:
            files.append(path)

    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def assert_safe_path(path: Path) -> None:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    suffix = path.suffix.lower()

    if parts & FORBIDDEN_PARTS:
        raise SystemExit(f"Blocked release path selected: {rel}")
    if suffix in BLOCKED_SUFFIXES:
        raise SystemExit(f"Sensitive or binary file selected: {rel}")


def zip_info(name: str, is_dir: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name if not is_dir else name.rstrip("/") + "/")
    info.date_time = (2024, 1, 1, 0, 0, 0)
    mode = stat.S_IFDIR | 0o755 if is_dir else stat.S_IFREG | 0o644
    info.external_attr = mode << 16
    return info


def build_zip(version: str) -> Path:
    release_files = iter_release_files()
    for path in release_files:
        assert_safe_path(path)

    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"opencareloop-{version}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zip_info(PACKAGE_ROOT, is_dir=True), "")
        zf.writestr(zip_info(f"{PACKAGE_ROOT}/people", is_dir=True), "")
        zf.writestr(zip_info(f"{PACKAGE_ROOT}/people/.gitkeep"), "")

        # Stamp the release version so the in-place updater can compare against
        # the latest published release.
        zf.writestr(zip_info(f"{PACKAGE_ROOT}/VERSION"), f"{version}\n")

        for path in release_files:
            rel = path.relative_to(ROOT).as_posix()
            arcname = f"{PACKAGE_ROOT}/{rel}"
            data = path.read_bytes()
            zf.writestr(zip_info(arcname), data)

    return zip_path


def main() -> int:
    version = normalized_version(parse_args().version)
    zip_path = build_zip(version)
    print(zip_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
