#!/usr/bin/env python3
"""Build the static GitHub Pages gallery from the themes in this repo.

Everything is baked at build time: theme metadata is read from each
``.peltontheme`` manifest and written into the page as JSON, and preview
images plus the ``.peltontheme`` files themselves are copied into the output.
The published site therefore makes **no** network or GitHub API calls at
runtime — it is fully self-contained and GDPR friendly.

Usage:
    python3 scripts/build_site.py            # build into _site/
    python3 scripts/build_site.py out/       # build into a custom dir

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO = "https://github.com/TRC-Loop/pelton-themes"
FOLDER_BASE = f"{REPO}/tree/main/themes"
CUSTOM_DOMAIN = "themes.pelton.app"

WEB = Path("web")
THEMES_DIR = Path("themes")

PREVIEW_EXTS = (".png", ".webp", ".jpg", ".jpeg", ".gif", ".avif", ".svg")


def read_manifest(pack: Path) -> dict | None:
    try:
        with zipfile.ZipFile(pack) as zf:
            if "manifest.json" not in zf.namelist():
                return None
            return json.loads(zf.read("manifest.json"))
    except (zipfile.BadZipFile, json.JSONDecodeError):
        return None


def extract_preview(pack: Path, manifest: dict, dest_dir: Path) -> str | None:
    """Copy the theme's preview image into dest_dir, return its filename."""
    preview = manifest.get("preview")
    if preview:
        try:
            with zipfile.ZipFile(pack) as zf:
                if preview in zf.namelist():
                    out_name = "preview" + Path(preview).suffix.lower()
                    (dest_dir / out_name).write_bytes(zf.read(preview))
                    return out_name
        except zipfile.BadZipFile:
            pass
    # Fall back to a preview.* file sitting next to the theme in its folder.
    folder = pack.parent
    for ext in PREVIEW_EXTS:
        cand = folder / ("preview" + ext)
        if cand.exists():
            out_name = "preview" + ext
            shutil.copy2(cand, dest_dir / out_name)
            return out_name
    return None


def collect_theme(folder: Path, out: Path) -> dict | None:
    packs = sorted(folder.glob("*.peltontheme"))
    if not packs:
        return None
    pack = packs[0]
    manifest = read_manifest(pack)
    if manifest is None:
        return None

    slug = folder.name
    asset_dir = out / "themes" / slug
    asset_dir.mkdir(parents=True, exist_ok=True)

    # Copy the downloadable file into the site (same-origin download).
    shutil.copy2(pack, asset_dir / pack.name)
    preview_name = extract_preview(pack, manifest, asset_dir)

    pel = manifest.get("pelton", {}) or {}
    return {
        "slug": slug,
        "name": manifest.get("name", slug),
        "author": manifest.get("author", ""),
        "description": manifest.get("description", ""),
        "base": manifest.get("base", "dark"),
        "version": manifest.get("version", ""),
        "peltonMin": pel.get("min", ""),
        "peltonMax": pel.get("max", ""),
        "license": manifest.get("license", ""),
        "file": pack.name,
        "download": f"themes/{slug}/{pack.name}",
        "preview": f"themes/{slug}/{preview_name}" if preview_name else None,
        "folder": f"{FOLDER_BASE}/{slug}",
    }


def collect_all(out: Path) -> list[dict]:
    if not THEMES_DIR.is_dir():
        return []
    themes = []
    for folder in sorted(THEMES_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "_")):
            continue
        data = collect_theme(folder, out)
        if data:
            themes.append(data)
    return themes


def render_html(themes: list[dict]) -> str:
    data = json.dumps(themes, ensure_ascii=False)
    count = len(themes)
    plural = "theme" if count == 1 else "themes"
    return TEMPLATE.replace("__THEMES_JSON__", data).replace(
        "__COUNT__", f"{count} {plural}"
    )


def build(out_dir: str) -> None:
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # Static assets (self-hosted: no external requests at runtime).
    shutil.copytree(WEB / "fonts", out / "fonts")
    shutil.copytree(WEB / "img", out / "img")
    shutil.copy2(WEB / "style.css", out / "style.css")
    shutil.copy2(WEB / "app.js", out / "app.js")

    themes = collect_all(out)
    (out / "index.html").write_text(render_html(themes), encoding="utf-8")
    # Tell Pages not to run Jekyll over our files.
    (out / ".nojekyll").write_text("", encoding="utf-8")
    # Custom domain for GitHub Pages.
    (out / "CNAME").write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")

    print(f"Built {len(themes)} theme(s) into {out}/")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pelton Themes</title>
<meta name="description" content="Community theme gallery for Pelton, the privacy-first email client. Browse, preview and download .peltontheme files.">
<link rel="icon" type="image/webp" href="./img/pelton-logo.webp">
<link rel="stylesheet" href="./style.css">
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="https://pelton.app">
      <img src="./img/pelton-logo.webp" alt="" width="26" height="26">
      <span>Pelton Themes</span>
    </a>
    <nav class="header-links">
      <a href="https://pelton.app">Website</a>
      <a href="https://docs.pelton.app/themes/">Theme docs</a>
      <a href="https://github.com/TRC-Loop/pelton-themes">GitHub</a>
    </nav>
  </div>
</header>

<main class="wrap">
  <section class="hero">
    <h1>Pelton Themes</h1>
    <p>The community gallery for <a href="https://pelton.app">Pelton</a>, the privacy-first email client. Browse, preview and download themes — then import them under Settings, Themes.</p>
    <div class="cta">
      <a class="btn btn-primary" href="https://github.com/TRC-Loop/pelton-themes/issues/new?template=submit_theme.yml">Submit a theme</a>
      <a class="btn btn-ghost" href="https://github.com/TRC-Loop/pelton-themes/blob/main/CONTRIBUTING.md">How it works</a>
    </div>
  </section>

  <div class="toolbar">
    <input type="search" id="search" placeholder="Search themes by name, author or description…" aria-label="Search themes">
    <span class="count" id="count">__COUNT__</span>
  </div>

  <div class="grid" id="grid"></div>
  <nav class="pagination" id="pagination" aria-label="Pagination"></nav>
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="footer-links">
      <a href="https://pelton.app">Website</a>
      <a href="https://docs.pelton.app">Documentation</a>
      <a href="https://docs.pelton.app/themes/">Theme docs</a>
      <a href="https://docs.pelton.app/themes/format/">Format spec</a>
      <a href="https://docs.pelton.app/themes/create/">Create a theme</a>
      <a href="https://github.com/TRC-Loop/Pelton">App repo</a>
      <a href="https://github.com/TRC-Loop/pelton.app">Website repo</a>
      <a href="https://github.com/TRC-Loop/pelton-themes">Themes repo</a>
      <a href="https://github.com/TRC-Loop/Pelton/releases">Releases</a>
      <a href="https://arne.sh/discord">Discord</a>
    </div>
    <div class="legal">
      &copy; Pelton. Themes are contributed by the community and licensed by their authors.
      <a href="https://pelton.app/imprint/en/">Imprint / Impressum</a> &middot;
      <a href="https://pelton.app/privacy/">Privacy / Datenschutz</a>
    </div>
  </div>
</footer>

<div class="modal-backdrop" id="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal">
    <h2 id="modal-title">Download this theme?</h2>
    <p class="modal-theme" id="modal-theme"></p>
    <div class="warn">
      <span>&#9888;&#65039;</span>
      <span><strong>Third-party content.</strong> Themes are community-submitted. We check every submission, but some things can slip through — a theme is code-adjacent, so treat it like anything you download from the internet. You install it at your own risk.</span>
    </div>
    <ul>
      <li>Pelton shows you the metadata and raw CSS before anything installs.</li>
      <li>Remote resources are flagged and stripped by default at import.</li>
      <li>Only import themes you are comfortable trusting.</li>
    </ul>
    <div class="modal-actions">
      <button class="btn btn-ghost" id="modal-cancel" type="button">Cancel</button>
      <button class="btn btn-primary" id="modal-confirm" type="button">I understand, download</button>
    </div>
  </div>
</div>

<script>window.__THEMES__ = __THEMES_JSON__;</script>
<script src="./app.js"></script>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    out = argv[0] if argv else "_site"
    build(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
