#!/usr/bin/env python3
"""
credit_author_statement_creator.py

Usage:
  python credit_author_statement_creator.py         → build docx from _temp/CreditAuthorStatement.json
  python credit_author_statement_creator.py --build → same (alias, always reads json)

_temp/CreditAuthorStatement.json format:
  [
    {"name": "Li Chao",        "roles": ["Conceptualization", "Methodology", ...]},
    {"name": "Mi Jie",         "roles": ["Review & Editing"]},
    ...
  ]

Required .input keys: article_link
Optional .input keys: credit_name (default: CreditAuthorStatement.docx)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR    = Path(__file__).parent
PROJECT_ROOT  = SCRIPT_DIR.parent
INPUT_FILE    = PROJECT_ROOT / ".input"
TEMPLATE_DOCX = PROJECT_ROOT / "CLASSICS" / "CreditAuthorStatement.docx"
TEMP_DIR      = PROJECT_ROOT / "_temp"
TEMP_JSON     = TEMP_DIR / "CreditAuthorStatement.json"

# Canonical role list (order preserved from template)
CREDIT_ROLES = [
    "Conceptualization",
    "Methodology",
    "Software",
    "Validation",
    "Formal analysis",
    "Investigation",
    "Data Curation",
    "Data Processing",
    "Original Draft",
    "Review & Editing",
    "Visualization",
    "Resources",
    "Supervision",
    "Project administration",
    "Funding acquisition",
]


# ---------------------------------------------------------------------------
# Parse .input
# ---------------------------------------------------------------------------
def parse_input(path: Path) -> dict:
    result: dict = {}
    content = path.read_text()
    for m in re.finditer(r'(\w+)\s*=\s*[{\[](.*?)[}\]]', content, re.DOTALL):
        items = [s.strip().strip("'\"") for s in m.group(2).split(',') if s.strip().strip("'\"")]
        result[m.group(1)] = items
    for line in content.splitlines():
        m = re.match(r"""(\w+)\s*=\s*['"]([^'"]+)['"]""", line.strip())
        if m and m.group(1) not in result:
            result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Build CreditAuthorStatement.docx from JSON
# ---------------------------------------------------------------------------
def build_docx(entries: list[dict], output_path: Path):
    import shutil
    from docx import Document

    shutil.copy2(str(TEMPLATE_DOCX), str(output_path))
    doc = Document(str(output_path))

    # Remove all existing author lines (para 2 onwards that have text)
    body = doc.element.body
    to_remove = [p._element for i, p in enumerate(doc.paragraphs) if i >= 2 and p.text.strip()]
    for el in to_remove:
        body.remove(el)

    # Append new author lines with same style as template
    for entry in entries:
        name  = entry.get("name", "").strip()
        roles = entry.get("roles", [])
        if not name or not roles:
            continue
        p = doc.add_paragraph(style="Acknowledgement")
        p.add_run(f"{name}: {', '.join(roles)}")

    doc.save(str(output_path))
    print(f"[✓] CreditAuthorStatement saved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not INPUT_FILE.exists():
        sys.exit(f"[Error] .input not found: {INPUT_FILE}")
    if not TEMPLATE_DOCX.exists():
        sys.exit(f"[Error] Template not found: {TEMPLATE_DOCX}")
    if not TEMP_JSON.exists():
        sys.exit(f"[Error] No JSON at {TEMP_JSON}. Fill in roles via the web UI first.")

    cfg          = parse_input(INPUT_FILE)
    article_link = cfg.get("article_link", "").strip()
    credit_name  = cfg.get("credit_name", "CreditAuthorStatement.docx").strip()

    if not article_link:
        sys.exit("[Error] .input must define article_link")

    entries = json.loads(TEMP_JSON.read_text(encoding="utf-8"))
    for e in entries:
        print(f"  {e['name']}: {', '.join(e['roles'])}")

    output_path = Path(article_link) / credit_name
    build_docx(entries, output_path)


if __name__ == "__main__":
    main()
