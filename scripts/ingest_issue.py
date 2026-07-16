#!/usr/bin/env python3
"""Turn a "Submit a theme" issue into files on disk for an automatic PR.

Reads the issue form body (GitHub renders each field as a ``### Label`` heading
followed by its value), finds the attached ``.zip``, downloads it into
``themes/<slug>/`` and writes a LICENSE and a starter README. A later CI step
(scripts/normalize_uploads.py) renames the ``.zip`` to ``.peltontheme``.

Inputs come from the environment:
    ISSUE_BODY    the raw issue body (markdown)
    ISSUE_NUMBER  the issue number (for messages)
    GH_TOKEN      optional token, used as a bearer for the download

Outputs are written to $GITHUB_OUTPUT as ``key=value`` lines:
    ok=true|false   whether a theme was ingested
    reason=...      why not, when ok=false
    slug=...        the theme slug / folder name
    name=...        the theme display name

No third-party dependencies: standard library only.
"""

from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path

NO_RESPONSE = {"", "_no response_", "_no response_.", "n/a", "none"}


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^#{2,4}\s+(.*)$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def find(sections: dict[str, str], *needles: str) -> str:
    for key, val in sections.items():
        if all(n in key for n in needles):
            v = val.strip()
            return "" if v.lower() in NO_RESPONSE else v
    return ""


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "theme"


def all_zip_urls(text: str) -> list[str]:
    # Markdown links or bare URLs pointing at .zip files, in order, deduped.
    urls: list[str] = []
    for m in re.finditer(r"https?://[^\s)\]]+", text):
        url = m.group(0)
        if url.lower().split("?")[0].endswith(".zip") and url not in urls:
            urls.append(url)
    return urls


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "pelton-themes-bot"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and ("github.com" in url or "githubusercontent.com" in url):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp, dest.open("wb") as fh:
        fh.write(resp.read())


def emit(**kw) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    lines = [f"{k}={v}" for k, v in kw.items()]
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    sections = parse_sections(body)

    name = find(sections, "theme", "name") or find(sections, "name")
    author = find(sections, "author") or "Unknown"
    license_id = find(sections, "license", "name") or find(sections, "license")
    license_text = find(sections, "license", "text") or find(sections, "full", "license")
    description = find(sections, "description")
    file_section = find(sections, "file") or find(sections, "theme", "file")

    urls = all_zip_urls(file_section) or all_zip_urls(body)
    if not name:
        emit(ok="false", reason="Could not find a theme name in the issue.")
        return 0
    if not urls:
        emit(ok="false", reason="Could not find an attached .zip in the issue.")
        return 0

    slug = slugify(name)
    folder = Path("themes") / slug
    folder.mkdir(parents=True, exist_ok=True)

    # Download every attached .zip (a theme can ship several flavors).
    used: set[str] = set()
    for i, url in enumerate(urls):
        zip_name = re.sub(r"[^A-Za-z0-9._-]", "-", Path(url.split("?")[0]).name)
        if not zip_name.lower().endswith(".zip"):
            zip_name = f"{slug}-{i + 1}.zip"
        while zip_name in used:
            zip_name = f"{Path(zip_name).stem}-{i + 1}.zip"
        used.add(zip_name)
        try:
            download(url, folder / zip_name)
        except Exception as exc:  # noqa: BLE001 - report any download failure
            emit(ok="false", reason=f"Failed to download {zip_name}: {exc}")
            return 0

    if license_text:
        (folder / "LICENSE").write_text(license_text.rstrip() + "\n", encoding="utf-8")
    else:
        (folder / "LICENSE").write_text(
            f"This theme is released under the {license_id or 'stated'} license "
            f"by {author}.\n\nThe full license text was not provided; please add it.\n",
            encoding="utf-8",
        )

    readme = f"## About\n\n{description or name}\n"
    if author and author != "Unknown":
        readme += f"\n_Submitted by {author}._\n"
    (folder / "README.md").write_text(readme, encoding="utf-8")

    emit(ok="true", slug=slug, name=name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
