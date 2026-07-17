#!/usr/bin/env python3
"""Render the generated metadata header into every theme's README.

Each ``themes/<name>/README.md`` gets a block of facts pulled straight from
the theme's ``.peltontheme`` manifest (version, Pelton compatibility, author,
license, and so on), followed by a ``---`` rule, followed by the author's own
README text. The block is regenerated on every run; everything the author
wrote below the marker is preserved untouched.

Usage:
    python3 scripts/render_readme.py            # rewrite every theme README
    python3 scripts/render_readme.py --check    # fail if any README is stale
    python3 scripts/render_readme.py themes/amber-marigold

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from themelib import theme_meta

START = "<!-- PELTON-META:START (generated from manifest.json by CI — do not edit inside this block) -->"
END = "<!-- PELTON-META:END -->"


def read_manifest(pack: Path) -> dict:
    with zipfile.ZipFile(pack) as zf:
        return json.loads(zf.read("manifest.json"))


def compat_text(pel: dict) -> str:
    lo, hi = pel.get("min"), pel.get("max")
    if lo and hi:
        return f"`{lo}` – `{hi}`"
    if lo:
        return f"`{lo}` or newer"
    if hi:
        return f"up to `{hi}`"
    return "any version"


def made_for_text(pel: dict) -> str:
    lo = pel.get("min")
    return f"Pelton `{lo}`" if lo else "unspecified"


def row(label: str, value: str) -> str:
    return f"| **{label}** | {value} |"


def render_block(folder: Path, packs: list[Path]) -> str:
    meta = theme_meta(folder, packs)
    manifests = [(p, read_manifest(p)) for p in packs]
    primary = manifests[0][1]

    lines: list[str] = [
        START,
        "> [!NOTE]",
        "> This section is generated automatically from the theme's "
        "`.peltontheme` manifest. Do not edit it by hand, change the theme "
        "and let CI re-render it.",
        "",
        f"# {meta['name']}",
    ]
    if meta["description"]:
        lines += ["", f"*{meta['description']}*"]

    lines += ["", "| Field | Value |", "| --- | --- |"]

    if meta["multi"]:
        lines += [
            row("Authors", ", ".join(meta["authors"]) or "—"),
            row("Licenses", ", ".join(f"`{lc}`" for lc in meta["licenses"]) or "—"),
            row("Bases", ", ".join(f"`{b}`" for b in meta["bases"]) or "—"),
            row("Flavors", str(len(meta["flavors"]))),
            "",
            "| Flavor | Version | Base | Made for | Package |",
            "| --- | --- | --- | --- | --- |",
        ]
        for pack, man in manifests:
            mp = man.get("pelton", {}) or {}
            lines.append(
                f"| {man.get('name', '—')} | `{man.get('version', '—')}` | "
                f"`{man.get('base', '—')}` | {made_for_text(mp)} | `{pack.name}` |"
            )
    else:
        pel = primary.get("pelton", {}) or {}
        lines += [
            row("Theme version", f"`{primary.get('version', '—')}`"),
            row("Made for", made_for_text(pel)),
            row("Compatibility", compat_text(pel)),
            row("Base", f"`{primary.get('base', '—')}`"),
            row("Author", primary.get("author", "—")),
            row("License", f"`{primary.get('license', 'see LICENSE')}`"),
            row("id", f"`{primary.get('id', folder.name)}`"),
        ]
        if primary.get("homepage"):
            lines.append(row("Homepage", f"<{primary['homepage']}>"))
        lines.append(row("Package", f"`{packs[0].name}`"))

    lines += ["", END]
    return "\n".join(lines)


def split_author(existing: str) -> str:
    """Return the author-written portion of an existing README."""
    if END in existing:
        after = existing.split(END, 1)[1]

        after = after.lstrip("\n")
        if after.startswith("---"):
            after = after[3:].lstrip("\n")
        return after
    return existing


def render_folder(folder: Path) -> tuple[str, str] | None:
    """Return (path, new_contents) or None if there is nothing to render."""
    packs = sorted(folder.glob("*.peltontheme"))
    if not packs:
        return None

    readme = folder / "README.md"
    existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
    author = split_author(existing).strip()
    if not author:
        author = (
            f"<!-- Write your theme's README below. Anything here is kept; "
            f"the block above is generated. Add screenshots, links, socials, "
            f"install notes, credits… -->\n"
        )

    block = render_block(folder, packs)
    new = f"{block}\n\n---\n\n{author}\n"
    return (readme.as_posix(), new)


def iter_theme_dirs(targets: list[str]) -> list[Path]:
    if targets:
        return [Path(t) for t in targets]
    root = Path("themes")
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def main(argv: list[str]) -> int:
    check = "--check" in argv
    targets = [a for a in argv if not a.startswith("--")]

    stale: list[str] = []
    for folder in iter_theme_dirs(targets):
        result = render_folder(folder)
        if result is None:
            continue
        path, new = result
        p = Path(path)
        current = p.read_text(encoding="utf-8") if p.exists() else ""
        if current == new:
            print(f"[ok]    {path}")
            continue
        if check:
            stale.append(path)
            print(f"[stale] {path}")
        else:
            p.write_text(new, encoding="utf-8")
            print(f"[write] {path}")

    if check and stale:
        print(f"\n{len(stale)} README(s) out of date. Run render_readme.py.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
