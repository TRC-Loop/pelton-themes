#!/usr/bin/env python3
"""A small, dependency-free Markdown to HTML renderer for theme READMEs."""

from __future__ import annotations

import html
import re

_CALLOUTS = {"note", "tip", "important", "warning", "caution"}
_LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")


def _inline(text: str) -> str:
    codes: list[str] = []

    def stash(m: "re.Match[str]") -> str:
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)",
        lambda m: f'<img src="{m.group(2)}" alt="{html.escape(m.group(1))}">',
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noreferrer noopener">{m.group(1)}</a>',
        text,
    )
    text = re.sub(
        r"<((?:https?)://[^>\s]+)>",
        lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noreferrer noopener">{m.group(1)}</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + codes[int(m.group(1))] + "</code>", text)
    return text


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _table(rows: list[str]) -> str:
    header = _cells(rows[0])
    parts = ["<table><thead><tr>"]
    parts += [f"<th>{_inline(c)}</th>" for c in header]
    parts.append("</tr></thead><tbody>")
    for r in rows[2:]:
        parts.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _quote(qlines: list[str]) -> str:
    first = qlines[0].strip() if qlines else ""
    m = re.match(r"^\[!(\w+)\]\s*(.*)$", first)
    if m and m.group(1).lower() in _CALLOUTS:
        kind = m.group(1).lower()
        rest = qlines[1:]
        if m.group(2).strip():
            rest = [m.group(2)] + rest
        body = " ".join(x.strip() for x in rest if x.strip())
        return (
            f'<div class="callout callout-{kind}">'
            f'<span class="callout-title">{kind.title()}</span>'
            f"<p>{_inline(body)}</p></div>"
        )
    body = " ".join(x.strip() for x in qlines if x.strip())
    return f"<blockquote>{_inline(body)}</blockquote>"


def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue

        m = re.match(r"^```(\w*)\s*$", s)
        if m:
            lang, i = m.group(1), i + 1
            code = []
            while i < n and lines[i].strip() != "```":
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + html.escape("\n".join(code)) + "</code></pre>")
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            out.append("<hr>")
            i += 1
            continue

        if s.startswith("<"):
            block = []
            while i < n and lines[i].strip() != "":
                block.append(lines[i])
                i += 1
            out.append("\n".join(block))
            continue

        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(_quote(quote))
            continue

        if "|" in s and i + 1 < n and re.match(r"^\s*\|?[\s:-]*-{2,}[\s:|-]*$", lines[i + 1]):
            tbl = []
            while i < n and "|" in lines[i] and lines[i].strip():
                tbl.append(lines[i])
                i += 1
            out.append(_table(tbl))
            continue

        if _LIST_RE.match(raw):
            ordered = bool(re.match(r"^\s*\d+\.\s+", raw))
            items = []
            while i < n and _LIST_RE.match(lines[i]):
                items.append(_LIST_RE.sub("", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + f"</{tag}>")
            continue

        para = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", ">", "<", "```")) and not _LIST_RE.match(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + _inline(" ".join(para)) + "</p>")

    return "\n".join(out)
