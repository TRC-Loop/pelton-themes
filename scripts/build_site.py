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

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from themelib import read_manifest, theme_meta
from mdrender import md_to_html

META_END = "<!-- PELTON-META:END -->"

REPO = "https://github.com/TRC-Loop/pelton-themes"
FOLDER_BASE = f"{REPO}/tree/main/themes"
CUSTOM_DOMAIN = "themes.pelton.app"

WEB = Path("web")
THEMES_DIR = Path("themes")

PREVIEW_EXTS = (".png", ".webp", ".jpg", ".jpeg", ".gif", ".avif", ".svg")


FONT_TOKENS = {"font-ui", "font-mono"}
TYPE_TOKENS = {
    "fz-meta", "fz-label", "fz-list", "fz-body", "fz-heading", "fz-title",
    "fw-regular", "fw-medium", "fw-semibold", "fw-bold",
}
RADIUS_TOKENS = {"radius-control", "radius-card", "radius-none"}
NON_COLOUR = FONT_TOKENS | TYPE_TOKENS | RADIUS_TOKENS

REMOTE_MARKERS = ("@import", "url(http", "url( http", 'url("http', "url('http", "url(//", 'url("//', "url('//")


def extract_pack_preview(pack: Path, manifest: dict, dest_dir: Path) -> tuple[str, str] | None:
    """Extract a pack's bundled preview into dest_dir.

    Returns (site_filename, content_hash) or None. The filename is derived from
    the pack name so each flavor's preview stays distinct.
    """
    preview = manifest.get("preview")
    if not preview:
        return None
    ext = Path(preview).suffix.lower()
    if ext not in PREVIEW_EXTS:
        return None
    try:
        with zipfile.ZipFile(pack) as zf:
            if preview not in zf.namelist():
                return None
            data = zf.read(preview)
    except zipfile.BadZipFile:
        return None
    out_name = pack.stem + ext
    (dest_dir / out_name).write_bytes(data)
    return out_name, hashlib.sha1(data).hexdigest()


def folder_preview(folder: Path, dest_dir: Path) -> str | None:
    """Copy a folder-level preview.* into dest_dir, return its filename."""
    for ext in PREVIEW_EXTS:
        cand = folder / ("preview" + ext)
        if cand.exists():
            shutil.copy2(cand, dest_dir / ("preview" + ext))
            return "preview" + ext
    return None


def detect_capabilities(pack: Path, manifest: dict) -> dict:
    """Work out what a theme actually alters, from its manifest and contents."""
    token_names: set[str] = set()
    css_blob = ""
    tokens = manifest.get("tokens")
    try:
        with zipfile.ZipFile(pack) as zf:
            names = zf.namelist()
            if isinstance(tokens, dict):
                token_names |= {k.lstrip("-") for k in tokens}
            elif isinstance(tokens, list):
                for entry in tokens:
                    if entry in names:
                        try:
                            obj = json.loads(zf.read(entry))
                            token_names |= {k.lstrip("-") for k in obj}
                        except json.JSONDecodeError:
                            pass
            for entry in manifest.get("css") or []:
                if entry in names:
                    css_blob += zf.read(entry).decode("utf-8", "replace").lower()
    except zipfile.BadZipFile:
        pass

    colours = bool(token_names - NON_COLOUR)
    fonts = bool(token_names & (FONT_TOKENS | TYPE_TOKENS)) or "@font-face" in css_blob
    icons = bool(manifest.get("icons"))
    css = bool(manifest.get("css"))
    external = any(m in css_blob for m in REMOTE_MARKERS)
    return {
        "colours": colours,
        "fonts": fonts,
        "icons": icons,
        "css": css,
        "external": external,
    }


def author_readme(folder: Path) -> str:
    readme = folder / "README.md"
    if not readme.exists():
        return ""
    text = readme.read_text(encoding="utf-8")
    if META_END in text:
        text = text.split(META_END, 1)[1].lstrip("\n")
        if text.startswith("---"):
            text = text[3:].lstrip("\n")
    text = text.strip()
    if not text or text.lstrip().startswith("<!--"):
        return ""
    return md_to_html(text)


def collect_theme(folder: Path, out: Path) -> dict | None:
    packs = sorted(folder.glob("*.peltontheme"))
    if not packs:
        return None
    meta = theme_meta(folder, packs)
    if not meta["flavors"]:
        return None

    slug = folder.name
    asset_dir = out / "themes" / slug
    asset_dir.mkdir(parents=True, exist_ok=True)

    previews: list[str] = []
    seen_previews: set[str] = set()
    flavors: list[dict] = []
    caps = {"colours": False, "fonts": False, "icons": False, "css": False, "external": False}

    for pack in packs:
        manifest = read_manifest(pack)
        if manifest is None:
            continue

        shutil.copy2(pack, asset_dir / pack.name)

        result = extract_pack_preview(pack, manifest, asset_dir)
        if result:
            name, digest = result
            if digest not in seen_previews:
                seen_previews.add(digest)
                previews.append(f"themes/{slug}/{name}")

        c = detect_capabilities(pack, manifest)
        for k in caps:
            caps[k] = caps[k] or c[k]

        pel = manifest.get("pelton", {}) or {}
        flavors.append({
            "name": manifest.get("name", pack.stem),
            "base": manifest.get("base", "dark"),
            "version": manifest.get("version", ""),
            "peltonMin": pel.get("min", ""),
            "file": pack.name,
            "download": f"themes/{slug}/{pack.name}",
        })


    if not previews:
        fp = folder_preview(folder, asset_dir)
        if fp:
            previews.append(f"themes/{slug}/{fp}")

    return {
        "slug": slug,
        "name": meta["name"],
        "author": meta["author"],
        "authors": meta["authors"],
        "description": meta["description"],
        "bases": meta["bases"],
        "version": meta["version"],
        "peltonMin": meta["peltonMin"],
        "license": meta["license"],
        "licenses": meta["licenses"],
        "multi": meta["multi"],
        "flavors": flavors,
        "previews": previews,
        "folder": f"{FOLDER_BASE}/{slug}",
        "caps": caps,
        "url": f"{slug}.html",
        "readme": author_readme(folder),
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


def asset_hash() -> str:
    """Short content hash of the CSS + JS, for cache-busting on every deploy."""
    h = hashlib.sha256()
    h.update((WEB / "style.css").read_bytes())
    h.update((WEB / "app.js").read_bytes())
    return h.hexdigest()[:10]


def render_gallery(themes: list[dict]) -> str:
    count = len(themes)
    plural = "theme" if count == 1 else "themes"
    slim = [{k: v for k, v in t.items() if k != "readme"} for t in themes]
    data = "window.__THEMES__ = " + json.dumps(slim, ensure_ascii=False).replace("<", "\\u003c") + ";"
    return (
        SHELL.replace("__TITLE__", "Pelton Themes")
        .replace("__DESC__", "Community theme gallery for Pelton, the privacy-first email client. Browse, preview and download .peltontheme files.")
        .replace("__BODY__", GALLERY_BODY.replace("__COUNT__", f"{count} {plural}"))
        .replace("__DATA__", data)
        .replace("__V__", asset_hash())
    )


def render_detail(theme: dict) -> str:
    data = "window.__THEME__ = " + json.dumps(theme, ensure_ascii=False).replace("<", "\\u003c") + ";"
    desc = theme.get("description") or f"{theme['name']}, a theme for Pelton."
    return (
        SHELL.replace("__TITLE__", f"{theme['name']} · Pelton Themes")
        .replace("__DESC__", desc.replace('"', "'"))
        .replace("__BODY__", DETAIL_BODY)
        .replace("__DATA__", data)
        .replace("__V__", asset_hash())
    )


def build(out_dir: str) -> None:
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)


    shutil.copytree(WEB / "fonts", out / "fonts")
    shutil.copytree(WEB / "img", out / "img")
    shutil.copy2(WEB / "style.css", out / "style.css")
    shutil.copy2(WEB / "app.js", out / "app.js")

    themes = collect_all(out)
    (out / "index.html").write_text(render_gallery(themes), encoding="utf-8")
    for theme in themes:
        (out / f"{theme['slug']}.html").write_text(render_detail(theme), encoding="utf-8")

    (out / ".nojekyll").write_text("", encoding="utf-8")

    (out / "CNAME").write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")

    print(f"Built {len(themes)} theme page(s) into {out}/")


SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="icon" type="image/webp" href="./img/pelton-logo.webp">
<link rel="stylesheet" href="./style.css?v=__V__">
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="./">
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

__BODY__

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
    <div class="flavor-picker" id="modal-flavors" hidden>
      <span class="flavor-label">Choose a flavor</span>
      <div class="flavor-options" id="modal-flavor-options"></div>
    </div>
    <div class="warn">
      <span>&#9888;&#65039;</span>
      <span><strong>Third-party content.</strong> Themes are community-submitted. We check every submission, but some things can slip through. A theme is code-adjacent, so treat it like anything you download from the internet. You install it at your own risk.</span>
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

<script>__DATA__</script>
<script src="./app.js?v=__V__"></script>
</body>
</html>
"""

GALLERY_BODY = """<main class="wrap">
  <section class="hero">
    <h1>Pelton Themes</h1>
    <p class="tagline">Community themes for <a href="https://pelton.app">Pelton</a>. Preview, download, import.</p>
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
</main>"""


DETAIL_BODY = """<main class="wrap theme-detail" id="theme-page"></main>"""


def main(argv: list[str]) -> int:
    out = argv[0] if argv else "_site"
    build(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
