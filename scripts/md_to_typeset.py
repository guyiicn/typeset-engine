"""Markdown → typeset JSON schema converter.

Converts a markdown string into the structured JSON expected by render_pdf /
render_docx. Used by the /render/pdf-md and /render/docx-md endpoints so callers
can hand in raw markdown instead of building the JSON tree themselves.

Supports:
  - H1/H2/H3 headings (nested under each other)
  - Paragraphs (blank-line separated)
  - Tables (markdown pipe tables, with header + separator row)
  - Code fences (rendered as quote blocks)
  - Horizontal rules (skipped)

Typst-safe escaping is applied to all rendered text, because Typst parses
table cell content AND paragraph content as markup. Without escaping, common
markdown content (e.g. `*.md`, `<addr>`, `$250K`, `# comment`) breaks the
Typst compile with "unclosed delimiter" or "unknown variable" errors.

Public API:
    convert(markdown: str, title: str, **payload_extra) -> dict
"""
from __future__ import annotations

import re


def escape_typst(text: str, *, cell: bool = False) -> str:
    """Escape Typst-special chars in plain text.

    Apply to every string that ends up in a heading title, paragraph, quote,
    or table cell. Order matters — backslash first.

    Special chars handled:
      `\\`  backslash  → must escape first (becomes `\\\\` in output)
      `#`   function call / variable
      `*`   bold toggle
      `_`   italic toggle
      `[ ]` content block
      `~`   no-break space
      `$`   math mode (huge surface — single `$` breaks rest of paragraph)
      `<>`  label syntax (not just escape — convert to fullwidth, double
            escaping by the JSON+template stack still trips Typst)

    Backticks are stripped in cells to clean up code-span markers like `addr`.
    """
    s = text
    s = s.replace("\\", "\\\\")
    s = s.replace("#", "\\#")
    s = s.replace("[", "\\[").replace("]", "\\]")
    s = s.replace("~", "\\~")
    # `<...>` triggers label syntax; fullwidth bypasses the parser entirely
    s = s.replace("<", "〈").replace(">", "〉")
    s = s.replace("*", "\\*").replace("_", "\\_")
    s = s.replace("$", "\\$")
    if cell:
        s = s.replace("`", "")
    return s


def _parse_table(lines: list[str], start: int) -> tuple[dict | None, int]:
    """Parse markdown pipe-table starting at lines[start]. Return (table_obj, next_idx)."""
    if "|" not in lines[start]:
        return None, start
    if start + 1 >= len(lines) or not re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[start + 1]):
        return None, start
    header_cells = [
        escape_typst(c.strip(), cell=True)
        for c in lines[start].strip().strip("|").split("|")
    ]
    rows = []
    i = start + 2
    while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
        cells = [
            escape_typst(c.strip(), cell=True)
            for c in lines[i].strip().strip("|").split("|")
        ]
        if len(cells) < len(header_cells):
            cells = cells + [""] * (len(header_cells) - len(cells))
        rows.append(cells[: len(header_cells)])
        i += 1
    return {"type": "table", "headers": header_cells, "rows": rows}, i


def _parse_md(content: str) -> list[dict]:
    """Convert markdown content → list of typeset section dicts.

    Builds a hierarchy from H1/H2/H3 (sub-headings become children of the
    nearest higher-level heading). Other content (paragraph/table/quote) is
    appended to the currently open heading's children, or to the root list
    if no heading is open.
    """
    lines = content.split("\n")
    root_sections: list[dict] = []
    stack: list[tuple[int, dict]] = []  # (level, heading_dict)

    def append(section: dict) -> None:
        if stack:
            stack[-1][1]["children"].append(section)
        else:
            root_sections.append(section)

    def flush_paragraph(buf: list[str]) -> None:
        if not buf:
            return
        content_str = "\n".join(buf).strip()
        if content_str:
            append({"type": "paragraph", "content": escape_typst(content_str)})
        buf.clear()

    para_buf: list[str] = []
    code_buf: list[str] = []
    in_code = False
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code fences ```
        if line.strip().startswith("```"):
            if in_code:
                flush_paragraph(para_buf)
                append({"type": "quote", "content": escape_typst("\n".join(code_buf))})
                code_buf = []
                in_code = False
            else:
                flush_paragraph(para_buf)
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Headings #/##/###
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            flush_paragraph(para_buf)
            level = len(m.group(1))
            title = escape_typst(m.group(2).strip().strip("`"), cell=True)
            new_h = {"type": "heading", "title": title, "children": []}
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack:
                stack[-1][1]["children"].append(new_h)
            else:
                root_sections.append(new_h)
            stack.append((level, new_h))
            i += 1
            continue

        # Tables
        if (
            "|" in line
            and i + 1 < len(lines)
            and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1])
        ):
            flush_paragraph(para_buf)
            tbl, ni = _parse_table(lines, i)
            if tbl:
                append(tbl)
                i = ni
                continue

        # Blank line = paragraph break
        if not line.strip():
            flush_paragraph(para_buf)
            i += 1
            continue

        # Horizontal rule
        if line.strip() == "---":
            flush_paragraph(para_buf)
            i += 1
            continue

        para_buf.append(line)
        i += 1

    flush_paragraph(para_buf)
    if in_code and code_buf:
        append({"type": "quote", "content": escape_typst("\n".join(code_buf))})

    return root_sections


def convert(markdown: str, title: str, **payload_extra) -> dict:
    """Convert markdown text → full typeset JSON payload.

    Caller can override author/date/toc via ``payload_extra`` (any field
    accepted by render_pdf / render_docx schema).
    """
    payload = {
        "title": escape_typst(title, cell=True),
        "toc": True,
        "sections": _parse_md(markdown),
    }
    payload.update(payload_extra)
    return payload
