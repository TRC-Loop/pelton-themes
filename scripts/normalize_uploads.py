#!/usr/bin/env python3
"""Rename uploaded ``.zip`` theme files back to ``.peltontheme``.

GitHub refuses ``.peltontheme`` attachments on issues, so contributors upload
their theme as a ``.zip`` (a ``.peltontheme`` is already a zip). When such a
file lands in a theme folder, this script renames it back to ``.peltontheme``
so the rest of the tooling and the gallery treat it normally.

Only zips that really are theme containers (``manifest.json`` at the root) are
touched; unrelated zips are left alone.

Usage:
    python3 scripts/normalize_uploads.py            # rename in every theme
    python3 scripts/normalize_uploads.py themes/foo # one folder

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

THEMES_DIR = Path("themes")


def is_theme_zip(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as zf:
            return "manifest.json" in zf.namelist()
    except zipfile.BadZipFile:
        return False


def iter_theme_dirs(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t) for t in targets]
    if not THEMES_DIR.is_dir():
        return []
    return sorted(
        p for p in THEMES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def normalize(folder: Path) -> list[str]:
    renamed = []
    for zip_path in sorted(folder.glob("*.zip")):
        if not is_theme_zip(zip_path):
            continue
        target = zip_path.with_suffix(".peltontheme")
        if target.exists():
            print(f"[skip]   {zip_path} -> {target.name} already exists")
            continue
        zip_path.rename(target)
        renamed.append(target.as_posix())
        print(f"[rename] {zip_path.as_posix()} -> {target.name}")
    return renamed


def main(argv: list[str]) -> int:
    renamed: list[str] = []
    for folder in iter_theme_dirs(argv):
        if folder.is_dir():
            renamed.extend(normalize(folder))
    if not renamed:
        print("Nothing to rename.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
