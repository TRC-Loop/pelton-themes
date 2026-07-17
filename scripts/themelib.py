#!/usr/bin/env python3
"""Shared helpers for reading themes and their (possibly multi-flavor) identity.

A theme folder holds one or more ``.peltontheme`` files. When it holds several
(different *flavors* of one theme), the folder needs a single theme-level name
and description rather than borrowing the first flavor's. That comes from, in
order of preference:

1. ``theme.json`` in the folder (``{"name": ..., "description": ...}``) — this
   is what the issue form fills in via scripts/ingest_issue.py.
2. The common prefix shared by every flavor's name / description.
3. A title-cased version of the folder slug.

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


_TRIM = " -–—:·|,.\t"


def read_manifest(pack: Path) -> dict | None:
    try:
        with zipfile.ZipFile(pack) as zf:
            if "manifest.json" not in zf.namelist():
                return None
            return json.loads(zf.read("manifest.json"))
    except (zipfile.BadZipFile, json.JSONDecodeError):
        return None


def _common_prefix(strings: list[str]) -> str:
    strings = [s for s in strings if s]
    if not strings:
        return ""
    lo, hi = min(strings), max(strings)
    i = 0
    while i < len(lo) and i < len(hi) and lo[i] == hi[i]:
        i += 1
    return lo[:i]


def _titleize(slug: str) -> str:
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug) if w) or slug


def _load_override(folder: Path) -> dict:
    tj = folder / "theme.json"
    if tj.exists():
        try:
            data = json.loads(tj.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def theme_meta(folder: Path, packs: list[Path]) -> dict:
    """Return theme-level display metadata for a folder of one or more packs."""
    manifests = [(p, read_manifest(p)) for p in packs]
    manifests = [(p, m) for p, m in manifests if m]

    flavors = []
    for p, m in manifests:
        pel = m.get("pelton", {}) or {}
        flavors.append(
            {
                "file": p.name,
                "name": m.get("name", p.stem),
                "description": m.get("description", ""),
                "base": m.get("base", "dark"),
                "version": m.get("version", ""),
                "peltonMin": pel.get("min", ""),
                "id": m.get("id", ""),
            }
        )

    multi = len(flavors) > 1
    override = _load_override(folder)

    if multi:
        name = (
            override.get("name")
            or _common_prefix([f["name"] for f in flavors]).strip(_TRIM)
            or _titleize(folder.name)
        )
        description = (
            override.get("description")
            or _common_prefix([f["description"] for f in flavors]).strip(_TRIM)
        )
    else:
        primary = flavors[0] if flavors else {}
        name = override.get("name") or primary.get("name") or _titleize(folder.name)
        description = override.get("description") or primary.get("description", "")

    bases = sorted({f["base"] for f in flavors})
    versions = {f["version"] for f in flavors if f["version"]}
    pelmins = {f["peltonMin"] for f in flavors if f["peltonMin"]}

    authors = _distinct(m.get("author", "") for _, m in manifests)
    licenses = _distinct(m.get("license", "") for _, m in manifests)

    return {
        "name": name,
        "description": description,
        "author": authors[0] if authors else "",
        "authors": authors,
        "license": licenses[0] if licenses else "",
        "licenses": licenses,
        "version": next(iter(versions)) if len(versions) == 1 else "",
        "peltonMin": next(iter(pelmins)) if len(pelmins) == 1 else "",
        "bases": bases,
        "multi": multi,
        "flavors": flavors,
    }


def _distinct(values) -> list[str]:
    out: list[str] = []
    for v in values:
        if v and v not in out:
            out.append(v)
    return out
