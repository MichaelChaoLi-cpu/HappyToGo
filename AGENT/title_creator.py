#!/usr/bin/env python3
"""
title_creator.py

Usage:
  python title_creator.py          → write _temp/Title.md then build Title.docx
  python title_creator.py --build  → build Title.docx from existing _temp/Title.md

_temp/Title.md format:
  # Title
  <manuscript title>

  # Authors
  Name[1], Name[1], CorrespondingName*[1]

  # Affiliations
  [1] Urban Institute & School of Engineering, Kyushu University, Japan

  # Corresponding
  Name | email@address | Full postal address

Required .input keys: article_link, file_name
Optional .input keys: title_name, authors, corresponding
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_FILE   = PROJECT_ROOT / ".input"
TEMPLATE_DOCX = PROJECT_ROOT / "CLASSICS" / "Title.docx"
TEMP_DIR     = PROJECT_ROOT / "_temp"
TEMP_MD      = TEMP_DIR / "Title.md"


# ---------------------------------------------------------------------------
# Parse .input
# ---------------------------------------------------------------------------
def parse_input(path: Path) -> dict:
    content = path.read_text()
    result: dict = {}
    for m in re.finditer(r'(\w+)\s*=\s*[{\[](.*?)[}\]]', content, re.DOTALL):
        key   = m.group(1)
        items = [s.strip().strip("'\"") for s in m.group(2).split(',') if s.strip().strip("'\"")]
        result[key] = items
    for line in content.splitlines():
        m = re.match(r"""(\w+)\s*=\s*['"]([^'"]+)['"]""", line.strip())
        if m and m.group(1) not in result:
            result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Extract manuscript title (first non-empty paragraph)
# ---------------------------------------------------------------------------
def extract_title(docx_path: Path) -> str:
    from docx import Document
    doc = Document(str(docx_path))
    return next((p.text.strip() for p in doc.paragraphs if p.text.strip()), "")


# ---------------------------------------------------------------------------
# Read full content from the template docx → dict of sections
# ---------------------------------------------------------------------------
def read_template_sections(template_path: Path) -> dict:
    from docx import Document
    doc = Document(str(template_path))
    paras = [p.text for p in doc.paragraphs]

    sections = {"title": "", "authors": "", "affiliations": [], "corresponding": ""}

    for i, text in enumerate(paras):
        t = text.strip()
        if i == 0:
            sections["title"] = t
        elif t == "Authors" and i + 1 < len(paras):
            sections["authors"] = paras[i + 1].strip()
        elif t.startswith("Affiliations") and i + 1 < len(paras):
            j = i + 1
            while j < len(paras) and paras[j].strip() and not paras[j].strip().startswith("*"):
                aff = paras[j].strip()
                # Template stores "1 Description" (superscript merged) → reformat as "[1] Description"
                m2 = re.match(r'^(\d+)\s+(.*)', aff)
                if m2:
                    aff = f"[{m2.group(1)}] {m2.group(2)}"
                sections["affiliations"].append(aff)
                j += 1
        elif t.startswith("* Correspondent to:"):
            raw = t.replace("* Correspondent to: ", "", 1)
            # raw = "Name, email, address" → convert to "Name | email | address"
            m2 = re.match(r'(.+?),\s*(\S+@\S+),\s*(.*)', raw)
            if m2:
                sections["corresponding"] = f"{m2.group(1)} | {m2.group(2)} | {m2.group(3)}"
            else:
                sections["corresponding"] = raw

    return sections


# ---------------------------------------------------------------------------
# Write _temp/Title.md with full content
# authors list: plain names; corresponding marked with *
# affiliations: list of "[N] Description" strings
# corresponding_text: "Name | email | address"
# ---------------------------------------------------------------------------
def write_temp_md(title: str, authors: list[str], corresponding: str,
                  affiliations: list[str], corresponding_text: str):
    TEMP_DIR.mkdir(exist_ok=True)

    author_line = ", ".join(
        f"{a}*[1]" if a == corresponding else f"{a}[1]"
        for a in authors
    )

    # Format affiliations block
    aff_block = "\n".join(affiliations) if affiliations else "[1] "

    md = (
        f"# Title\n{title}\n\n"
        f"# Authors\n{author_line}\n\n"
        f"# Affiliations\n{aff_block}\n\n"
        f"# Corresponding\n{corresponding_text}\n"
    )
    TEMP_MD.write_text(md, encoding="utf-8")
    print(f"[→] Markdown saved: {TEMP_MD}")


# ---------------------------------------------------------------------------
# Parse _temp/Title.md → dict with title / authors / corresponding / affiliations
# ---------------------------------------------------------------------------
def read_temp_md() -> dict:
    text = TEMP_MD.read_text(encoding="utf-8")

    def get_section(name: str) -> str:
        m = re.search(rf"^# {name}\s*\n(.*?)(?=^# |\Z)", text, re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    title        = get_section("Title")
    authors_raw  = get_section("Authors")
    aff_raw      = get_section("Affiliations")
    corr_raw     = get_section("Corresponding")

    # Parse authors: "Name*[N]" or "Name[N]"
    authors      = []
    corresponding = ""
    aff_map      = {}   # name → affiliation number

    for token in re.split(r",\s*", authors_raw):
        token = token.strip()
        if not token:
            continue
        # extract affiliation number [N]
        m = re.search(r"\[(\d+)\]", token)
        aff_num = m.group(1) if m else "1"
        name = re.sub(r"\[\d+\]", "", token).rstrip("*").strip()
        is_corr = "*" in token.replace(f"[{aff_num}]", "")
        authors.append(name)
        aff_map[name] = aff_num
        if is_corr:
            corresponding = name

    if not corresponding and authors:
        corresponding = authors[-1]

    # Parse affiliations: "[N] Description"
    affiliations = []
    for line in aff_raw.splitlines():
        line = line.strip()
        if line:
            affiliations.append(line)

    # Parse corresponding: "Name | email | address"
    corr_parts = [p.strip() for p in corr_raw.split("|")]
    corr_name    = corr_parts[0] if len(corr_parts) > 0 else corresponding
    corr_email   = corr_parts[1] if len(corr_parts) > 1 else ""
    corr_address = corr_parts[2] if len(corr_parts) > 2 else ""

    return {
        "title": title,
        "authors": authors,
        "corresponding": corresponding,
        "aff_map": aff_map,
        "affiliations": affiliations,
        "corr_name": corr_name,
        "corr_email": corr_email,
        "corr_address": corr_address,
    }


# ---------------------------------------------------------------------------
# Apply to docx
# ---------------------------------------------------------------------------
def update_title(doc, title: str):
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        r0 = para.runs[0]
        bold, size, fname = r0.bold, r0.font.size, r0.font.name
        for r in para.runs:
            r.text = ""
        r0.text  = title
        r0.bold  = bold
        r0.font.size = size
        if fname:
            r0.font.name = fname
        break


def update_authors_para(doc, authors: list[str], aff_map: dict, corresponding: str):
    authors_para = None
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip() == "Authors" and i + 1 < len(doc.paragraphs):
            authors_para = doc.paragraphs[i + 1]
            break
    if authors_para is None:
        print("[!] Authors paragraph not found")
        return

    for run in list(authors_para.runs):
        run._element.getparent().remove(run._element)

    def add_run(para, text, superscript=False):
        r = para.add_run(text)
        if superscript:
            r.font.superscript = True

    for i, name in enumerate(authors):
        display = f"{name}*" if name == corresponding else name
        add_run(authors_para, display)
        add_run(authors_para, aff_map.get(name, "1"), superscript=True)
        if i < len(authors) - 1:
            add_run(authors_para, ", ")


def update_affiliations(doc, affiliations: list[str]):
    """Replace each affiliation line. [N] prefix → superscript N."""
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip().startswith("Affiliations"):
            # Collect the affiliation paragraphs that follow
            aff_paras = []
            j = i + 1
            while j < len(doc.paragraphs) and doc.paragraphs[j].text.strip() \
                    and not doc.paragraphs[j].text.strip().startswith("*"):
                aff_paras.append(doc.paragraphs[j])
                j += 1

            # Update existing paragraphs or just update in place
            for k, aff_line in enumerate(affiliations):
                m = re.match(r"\[(\d+)\]\s*(.*)", aff_line)
                num  = m.group(1) if m else str(k + 1)
                desc = m.group(2) if m else aff_line

                if k < len(aff_paras):
                    para_aff = aff_paras[k]
                    for run in list(para_aff.runs):
                        run._element.getparent().remove(run._element)
                    r = para_aff.add_run(num)
                    r.font.superscript = True
                    para_aff.add_run(f" {desc}")
            break


def update_corresponding_line(doc, corr_name: str, corr_email: str, corr_address: str):
    from docx.oxml.ns import qn

    for para in doc.paragraphs:
        if not para.text.startswith("* Correspondent to:"):
            continue

        # Update run[1]: "Correspondent to: Name, "
        for run in para.runs:
            if run.text.startswith("Correspondent to:"):
                run.text = f"Correspondent to: {corr_name}, "
                break

        # Update hyperlink text (email)
        if corr_email:
            for child in para._element:
                if child.tag.endswith("}hyperlink"):
                    for t_elem in child.iter(qn("w:t")):
                        t_elem.text = corr_email
                    break

        # Update address: collapse all remaining runs (after hyperlink) into one
        if corr_address:
            runs_after = []
            found_hyperlink = False
            for child in para._element:
                tag = child.tag.split("}")[-1]
                if tag == "hyperlink":
                    found_hyperlink = True
                elif found_hyperlink and tag == "r":
                    runs_after.append(child)

            if runs_after:
                # Set first run to ", address", clear the rest
                from docx.oxml.ns import qn as _qn
                first_t = runs_after[0].find(_qn("w:t"))
                if first_t is not None:
                    first_t.text = f", {corr_address}"
                for r in runs_after[1:]:
                    t = r.find(_qn("w:t"))
                    if t is not None:
                        t.text = ""
        break


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    build_only = "--build" in sys.argv

    if not INPUT_FILE.exists():
        sys.exit(f"[Error] .input not found: {INPUT_FILE}")
    if not TEMPLATE_DOCX.exists():
        sys.exit(f"[Error] Template not found: {TEMPLATE_DOCX}")

    cfg          = parse_input(INPUT_FILE)
    article_link = (cfg.get("article_link") or "").strip()
    file_name    = (cfg.get("file_name") or "").strip()
    title_name   = (cfg.get("title_name") or "Title.docx").strip()

    if not article_link or not file_name:
        sys.exit("[Error] .input must define article_link and file_name")

    manuscript_path = Path(article_link) / file_name
    if not manuscript_path.exists():
        sys.exit(f"[Error] Manuscript not found: {manuscript_path}")

    output_path = Path(article_link) / title_name

    if build_only:
        if not TEMP_MD.exists():
            sys.exit(f"[Error] No markdown found at {TEMP_MD}. Run without --build first.")
        print(f"[→] Using existing markdown: {TEMP_MD}")
    else:
        # Pull base data
        title = extract_title(manuscript_path)
        tmpl  = read_template_sections(TEMPLATE_DOCX)

        # Authors from .input; fall back to template
        authors: list[str] = cfg.get("authors") or []
        corresponding: str = (cfg.get("corresponding") or "").strip()

        if not authors:
            # Parse template author line: "Chao Li1, ..."  (superscripts merged into text)
            raw = tmpl["authors"]
            authors = [re.sub(r"\d+$", "", a.rstrip("*").strip()) for a in raw.split(",")]
            corresponding = next(
                (re.sub(r"\d+$", "", a.rstrip("*").strip()) for a in raw.split(",") if "*" in a),
                authors[-1] if authors else ""
            )
        elif not corresponding:
            corresponding = authors[-1]

        # Build corresponding_text from template (already "Name | email | address")
        corr_text = tmpl["corresponding"]
        # Replace name part (before first |) with the actual corresponding author
        corr_text = re.sub(r"^[^|]+", f"{corresponding} ", corr_text)

        write_temp_md(title, authors, corresponding, tmpl["affiliations"], corr_text)

    # Read (possibly edited) markdown and build docx
    data = read_temp_md()
    print(f"[→] Title:        {data['title'][:70]}...")
    print(f"[→] Authors:      {data['authors']}")
    print(f"[→] Corresponding:{data['corresponding']}")

    shutil.copy2(str(TEMPLATE_DOCX), str(output_path))

    from docx import Document
    doc = Document(str(output_path))

    update_title(doc, data["title"])
    update_authors_para(doc, data["authors"], data["aff_map"], data["corresponding"])
    update_affiliations(doc, data["affiliations"])
    update_corresponding_line(doc, data["corr_name"], data["corr_email"], data["corr_address"])

    doc.save(str(output_path))
    print(f"[✓] Title page saved: {output_path}")

    # Copy DeclarationStatement.docx from CLASSICS to the manuscript folder
    decl_src = PROJECT_ROOT / "CLASSICS" / "DeclarationStatement.docx"
    decl_dst = Path(article_link) / "DeclarationStatement.docx"
    if decl_src.exists():
        shutil.copy2(str(decl_src), str(decl_dst))
        print(f"[✓] DeclarationStatement copied: {decl_dst}")
    else:
        print(f"[!] DeclarationStatement.docx not found in CLASSICS — skipping")


if __name__ == "__main__":
    main()
