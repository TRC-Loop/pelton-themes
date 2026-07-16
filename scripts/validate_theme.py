#!/usr/bin/env python3
"""Validate every theme in the pelton-themes repository.

A theme lives in ``themes/<name>/`` and ships one or more ``.peltontheme``
files (zip containers). This script mirrors the checks Pelton runs at import
time so a broken theme is caught in CI instead of on a user's machine.

Usage:
    python3 scripts/validate_theme.py                # validate every theme
    python3 scripts/validate_theme.py themes/nordish # validate one folder

Exit code is non-zero if any error is found. Warnings never fail the build.
No third-party dependencies: standard library only.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

# --- The themeable token surface (docs.pelton.app/themes/format) ------------
ALLOWED_TOKENS = {
    # Surfaces
    "surface-base", "surface-raised", "surface-overlay", "surface-sunken",
    "surface-hover", "selection-bg", "selection-bg-strong",
    # Text
    "text-primary", "text-secondary", "text-tertiary", "text-inverse", "link",
    # Borders
    "border-subtle", "border-default", "border-strong", "hairline",
    # Accent
    "accent", "accent-fg",
    # Semantic
    "success", "success-bg", "warning", "warning-bg", "danger", "danger-bg",
    # Radii
    "radius-control", "radius-card", "radius-none",
    # Fonts
    "font-ui", "font-mono",
    # Type
    "fz-meta", "fz-label", "fz-list", "fz-body", "fz-heading", "fz-title",
    "fw-regular", "fw-medium", "fw-semibold", "fw-bold",
    # Elevation
    "shadow-overlay",
}

# --- Size caps (bytes) ------------------------------------------------------
MAX_CONTAINER = 20 * 1024 * 1024
MAX_CSS_TOTAL = 1 * 1024 * 1024
MAX_ASSET = 5 * 1024 * 1024

ID_RE = re.compile(r"^[a-z0-9-]+$")
SEMVER_ISH = re.compile(r"^\d+(\.\d+){0,3}$")
# Remote references that would trigger Pelton's tracking warning.
REMOTE_IMPORT_RE = re.compile(r"@import\b", re.IGNORECASE)
REMOTE_URL_RE = re.compile(r"""url\(\s*['"]?\s*(?:https?:)?//""", re.IGNORECASE)


class Reporter:
    def __init__(self, scope: str) -> None:
        self.scope = scope
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(f"{self.scope}: {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(f"{self.scope}: {msg}")


def _norm_token(name: str) -> str:
    return name[2:] if name.startswith("--") else name


def _bad_token_value(value: str) -> bool:
    # Values may not contain semicolons, braces, @ or url() (docs: Tokens).
    return any(ch in value for ch in ";{}@") or "url(" in value.replace(" ", "").lower()


def validate_pack(pack: Path, rep: Reporter) -> None:
    if pack.stat().st_size > MAX_CONTAINER:
        rep.error(f"container exceeds 20 MB ({pack.stat().st_size} bytes)")

    try:
        zf = zipfile.ZipFile(pack)
    except zipfile.BadZipFile:
        rep.error("is not a valid zip container")
        return

    with zf:
        names = zf.namelist()
        if "manifest.json" not in names:
            rep.error("manifest.json must sit at the container root")
            return

        try:
            manifest = json.loads(zf.read("manifest.json"))
        except json.JSONDecodeError as exc:
            rep.error(f"manifest.json is not valid JSON ({exc})")
            return

        # -- Required manifest fields ------------------------------------
        if manifest.get("manifestVersion") != 1:
            rep.error("manifestVersion must be 1")
        if not manifest.get("name"):
            rep.error("name is required")
        base = manifest.get("base")
        if base not in ("light", "dark"):
            rep.error('base is required and must be "light" or "dark"')

        # -- Optional-but-checked fields ---------------------------------
        theme_id = manifest.get("id")
        if theme_id is not None and not ID_RE.match(str(theme_id)):
            rep.error(f'id "{theme_id}" must match a-z, 0-9 and dashes only')
        pel = manifest.get("pelton", {})
        for key in ("min", "max"):
            if key in pel and not SEMVER_ISH.match(str(pel[key])):
                rep.warn(f'pelton.{key} "{pel[key]}" does not look like a version')

        # -- Tokens ------------------------------------------------------
        _validate_tokens(manifest, zf, names, rep)

        # -- CSS ---------------------------------------------------------
        _validate_css(manifest, zf, names, rep)

        # -- Preview (recommended, not required) -------------------------
        preview = manifest.get("preview")
        if not preview:
            rep.warn("no preview image set (recommended for the gallery)")
        elif preview not in names:
            rep.error(f'preview "{preview}" is not in the container')

        # -- Per-asset size cap ------------------------------------------
        for info in zf.infolist():
            if info.filename.endswith(".css") or info.filename == "manifest.json":
                continue
            if info.file_size > MAX_ASSET:
                rep.error(f"asset {info.filename} exceeds 5 MB")


def _collect_token_maps(manifest, zf, names, rep) -> list[dict]:
    tokens = manifest.get("tokens")
    if tokens is None:
        return []
    if isinstance(tokens, dict):
        return [tokens]
    maps: list[dict] = []
    for entry in tokens:
        if entry not in names:
            rep.error(f"tokens file {entry} is not in the container")
            continue
        try:
            maps.append(json.loads(zf.read(entry)))
        except json.JSONDecodeError as exc:
            rep.error(f"tokens file {entry} is not valid JSON ({exc})")
    return maps


def _validate_tokens(manifest, zf, names, rep) -> None:
    for tmap in _collect_token_maps(manifest, zf, names, rep):
        for raw_name, value in tmap.items():
            name = _norm_token(raw_name)
            if name not in ALLOWED_TOKENS:
                rep.error(f'unknown token "{raw_name}" (not on the allowlist)')
            if _bad_token_value(str(value)):
                rep.error(f'token "{raw_name}" has an unsafe value: {value!r}')


def _validate_css(manifest, zf, names, rep) -> None:
    css_files = manifest.get("css") or []
    total = 0
    for entry in css_files:
        if entry not in names:
            rep.error(f"css file {entry} is not in the container")
            continue
        body = zf.read(entry).decode("utf-8", "replace")
        total += len(body.encode("utf-8"))
        if REMOTE_IMPORT_RE.search(body):
            rep.error(f"{entry} uses @import; bundle the resource instead")
        if REMOTE_URL_RE.search(body):
            rep.error(f"{entry} references a remote url(); bundle it instead")
    if total > MAX_CSS_TOTAL:
        rep.error(f"CSS totals {total} bytes, over the 1 MB cap")


def validate_theme_dir(folder: Path) -> Reporter:
    rep = Reporter(folder.as_posix())

    if not (folder / "LICENSE").exists() and not any(folder.glob("LICENSE*")):
        rep.error("a LICENSE file is required in every theme folder")

    readmes = list(folder.glob("README.*")) + list(folder.glob("readme.*"))
    if not readmes:
        rep.warn("no README found (recommended)")

    packs = sorted(folder.glob("*.peltontheme"))

    # A theme uploaded through the issue form arrives as a .zip (GitHub rejects
    # .peltontheme attachments). Accept a .zip that is really a theme container;
    # CI renames it to .peltontheme on merge (scripts/normalize_uploads.py).
    zip_packs = [z for z in sorted(folder.glob("*.zip")) if _is_theme_zip(z)]
    for z in zip_packs:
        rep.warn(f"{z.name} will be renamed to .peltontheme by CI")

    all_packs = packs + zip_packs
    if not all_packs:
        rep.error("no .peltontheme file found in the folder")
    for pack in all_packs:
        validate_pack(pack, rep)

    return rep


def _is_theme_zip(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as zf:
            return "manifest.json" in zf.namelist()
    except zipfile.BadZipFile:
        return False


def iter_theme_dirs(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t) for t in targets]
    root = Path("themes")
    if not root.is_dir():
        return []
    # Skip helpers like _TEMPLATE and any dot/underscore folder.
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def main(argv: list[str]) -> int:
    dirs = iter_theme_dirs(argv)
    if not dirs:
        print("No themes to validate.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    for folder in dirs:
        if not folder.is_dir():
            errors.append(f"{folder}: not a directory")
            continue
        rep = validate_theme_dir(folder)
        errors.extend(rep.errors)
        warnings.extend(rep.warnings)
        status = "FAIL" if rep.errors else "ok"
        print(f"[{status}] {folder.as_posix()}")

    for w in warnings:
        print(f"::warning:: {w}")
    for e in errors:
        print(f"::error:: {e}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"\nAll good. {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
