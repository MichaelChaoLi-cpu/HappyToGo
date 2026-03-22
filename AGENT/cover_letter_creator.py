#!/usr/bin/env python3
"""
cover_letter_creator.py

Flow:
  1. Read .input → locate manuscript docx
  2. Call Gemini → save markdown to _temp/CoverLetter.md
  3. Convert markdown → CoverLetter.docx via pandoc (pypandoc)

Required .input keys:
  article_link   path to the manuscript folder
  file_name      manuscript filename (e.g. ZDP02m-manu.docx)

Optional .input keys:
  journal_name       target journal (default: [TARGET JOURNAL])
  cover_letter_name  output filename (default: CoverLetter.docx)
"""

from __future__ import annotations

import os
import sys
import re
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_FILE = PROJECT_ROOT / ".input"
CLASSICS_DIR = PROJECT_ROOT / "CLASSICS"
TEMPLATE_DOCX = CLASSICS_DIR / "CoverLetter.docx"
TEMP_DIR = PROJECT_ROOT / "_temp"

sys.path.insert(0, str(SCRIPT_DIR))
from llm import call_llm  # noqa: E402


# ---------------------------------------------------------------------------
# Load .env if GEMINI_API_KEY not already set
# ---------------------------------------------------------------------------
def _load_env():
    env_file = PROJECT_ROOT / ".env"
    if os.environ.get("GEMINI_API_KEY"):
        return
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


# ---------------------------------------------------------------------------
# Parse .input
# ---------------------------------------------------------------------------
def parse_input(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(r"""(\w+)\s*=\s*['"]?([^'"#\n]+?)['"]?\s*$""")
    for line in path.read_text().splitlines():
        m = pattern.match(line.strip())
        if m:
            result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Extract text from manuscript docx
# ---------------------------------------------------------------------------
def extract_docx_text(docx_path: Path, max_chars: int = 6000) -> str:
    from docx import Document
    doc = Document(str(docx_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)[:max_chars]


def extract_docx_title(docx_path: Path, fallback: str) -> str:
    from docx import Document
    doc = Document(str(docx_path))
    return next((p.text.strip() for p in doc.paragraphs if p.text.strip()), fallback)


# ---------------------------------------------------------------------------
# Read signature block from CLASSICS/CoverLetter.docx
# ---------------------------------------------------------------------------
def read_template_signature(template_path: Path) -> list[str]:
    from docx import Document
    doc = Document(str(template_path))
    lines = [p.text for p in doc.paragraphs]
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("sincerely"):
            return [l for l in lines[i + 1:] if l.strip()]
    return []


# ---------------------------------------------------------------------------
# Step 1: Gemini → Markdown
# ---------------------------------------------------------------------------
def generate_markdown(
    manuscript_text: str,
    manuscript_title: str,
    journal_name: str,
    today_str: str,
    signature_lines: list[str],
) -> str:
    signature_block = "\n\n".join(signature_lines)

    prompt = f"""You are an expert academic editor. Write a complete cover letter for a journal submission in Markdown format.

MANUSCRIPT TITLE:
{manuscript_title}

TARGET JOURNAL:
{journal_name}

DATE:
{today_str}

MANUSCRIPT CONTENT (excerpt):
{manuscript_text}

OUTPUT FORMAT (strict Markdown, reproduce this structure exactly, replacing only the bracketed placeholders):

---
{manuscript_title}

{journal_name}

{today_str}

Dear Editor,

[Paragraph 1: Introduce the manuscript, its scope, data, and methods. Plain prose, no bullet points.]

[Paragraph 2: Summarize 2-3 key findings. Plain prose, no bullet points.]

[Paragraph 3: Explain the methodological and substantive contributions.]

[Paragraph 4: Explain why it fits the journal and invite the editor to reach out.]

Thank you for considering our manuscript. We look forward to your feedback and are eager to contribute to advancing research in this field.

Sincerely,

{signature_block}
---

RULES:
- Keep the first three lines exactly as shown: manuscript title, journal name, date — do not omit them.
- Replace the bracketed placeholders with real content based on the manuscript.
- Write in formal academic prose. No bullet points. No numbered lists.
- Do NOT add any headings (no # ## ###).
- Do NOT use bold (**text**) anywhere.
- Do NOT use italic (*text* or _text_) anywhere.
- Keep each paragraph as a single unbroken block of text.
- For the signature block, put each line on its own line with a single newline (not a blank line) between them.
- Output ONLY the content between the --- markers (do not include the --- lines themselves).
"""

    return call_llm(prompt).strip()


# ---------------------------------------------------------------------------
# Strip any residual markdown emphasis from a string (pre-pandoc)
# ---------------------------------------------------------------------------
def strip_markdown_emphasis(text: str) -> str:
    # Must strip bold before italic to avoid leaving stray *
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'__(.+?)__', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\*(.+?)\*', r'\1', text, flags=re.DOTALL)
    # Only strip _word_ at word boundaries to avoid mangling emails/filenames
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text, flags=re.DOTALL)
    return text


# ---------------------------------------------------------------------------
# Step 2: Markdown → docx via pandoc
# ---------------------------------------------------------------------------
def markdown_to_docx(md_path: Path, docx_path: Path):
    import pypandoc
    pypandoc.convert_file(
        str(md_path),
        "docx",
        outputfile=str(docx_path),
        extra_args=["--wrap=none"],
    )


# ---------------------------------------------------------------------------
# Step 3: Post-process docx — remove all italic, bold header lines
# ---------------------------------------------------------------------------
def postprocess_docx(docx_path: Path):
    from docx import Document

    doc = Document(str(docx_path))

    bolded = 0
    for para in doc.paragraphs:
        is_header = para.text.strip() and bolded < 2

        for run in para.runs:
            # Strip italic everywhere
            run.italic = False
            # Bold only the first two non-empty paragraphs (title + journal)
            if is_header:
                run.bold = True

        # Handle paragraphs where pandoc created no runs
        if not para.runs and para.text.strip():
            text = para.text
            para.clear()
            run = para.add_run(text)
            run.italic = False
            if is_header:
                run.bold = True

        if is_header:
            bolded += 1

    doc.save(str(docx_path))


# ---------------------------------------------------------------------------
# Main
# Usage:
#   python cover_letter_creator.py           → generate md (Gemini) then convert
#   python cover_letter_creator.py --build   → convert existing md only (skip Gemini)
# ---------------------------------------------------------------------------
def main():
    _load_env()

    build_only = "--build" in sys.argv

    if not INPUT_FILE.exists():
        sys.exit(f"[Error] .input file not found: {INPUT_FILE}")

    cfg = parse_input(INPUT_FILE)
    article_link = cfg.get("article_link", "").strip()
    file_name = cfg.get("file_name", "").strip()
    journal_name = cfg.get("journal_name", "[TARGET JOURNAL]").strip()
    cover_letter_name = cfg.get("cover_letter_name", "CoverLetter.docx").strip()

    if not article_link or not file_name:
        sys.exit("[Error] .input must define article_link and file_name")

    manuscript_path = Path(article_link) / file_name
    if not manuscript_path.exists():
        sys.exit(f"[Error] Manuscript not found: {manuscript_path}")

    output_path = Path(article_link) / cover_letter_name
    TEMP_DIR.mkdir(exist_ok=True)
    temp_md = TEMP_DIR / "CoverLetter.md"

    if build_only:
        # --build: skip Gemini, use the existing markdown as-is
        if not temp_md.exists():
            sys.exit(f"[Error] No markdown found at {temp_md}. Run without --build first.")
        print(f"[→] Using existing markdown: {temp_md}")
    else:
        # Full run: call Gemini and write fresh markdown
        manuscript_text = extract_docx_text(manuscript_path)
        manuscript_title = extract_docx_title(manuscript_path, file_name)
        print(f"[→] Title: {manuscript_title[:80]}...")
        print(f"[→] Journal: {journal_name}")

        signature_lines = []
        if TEMPLATE_DOCX.exists():
            signature_lines = read_template_signature(TEMPLATE_DOCX)
            print(f"[→] Loaded {len(signature_lines)} signature lines from template")

        d = date.today()
        suffix = "th" if 11 <= d.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d.day % 10, "th")
        today_str = d.strftime(f"%B {d.day}{suffix}, %Y")

        print("[→] Calling Gemini to generate markdown...")
        md_content = generate_markdown(
            manuscript_text, manuscript_title, journal_name, today_str, signature_lines
        )
        md_content = strip_markdown_emphasis(md_content)
        temp_md.write_text(md_content, encoding="utf-8")
        print(f"[→] Markdown saved: {temp_md}")

    print("[→] Converting markdown → docx via pandoc...")
    markdown_to_docx(temp_md, output_path)

    print("[→] Post-processing docx (remove italic, bold headers)...")
    postprocess_docx(output_path)
    print(f"[✓] Cover letter saved: {output_path}")


if __name__ == "__main__":
    main()
