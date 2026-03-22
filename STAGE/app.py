#!/usr/bin/env python3
"""
STAGE/app.py  —  HappyToGo document generation web UI
Run: python STAGE/app.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request

PROJECT_ROOT = Path(__file__).parent.parent
AGENT_DIR    = PROJECT_ROOT / "AGENT"
TEMP_DIR     = PROJECT_ROOT / "_temp"
INPUT_FILE   = PROJECT_ROOT / ".input"
CLASSICS_DIR = PROJECT_ROOT / "CLASSICS"

PYTHON = sys.executable   # same interpreter that's running this app

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MD_FILES = {
    "title":        "Title.md",
    "cover_letter": "CoverLetter.md",
    "highlights":   "Highlights.md",
}

SCRIPTS = {
    "title":        "title_creator.py",
    "cover_letter": "cover_letter_creator.py",
    "highlights":   "highlight_creator.py",
}

def run_script(script_name: str, extra_args: list[str] = []) -> dict:
    script = AGENT_DIR / script_name
    env_file = PROJECT_ROOT / ".env"

    # Build command: source .env is shell-specific; instead load vars manually
    import os
    env = os.environ.copy()
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if "=" in line and not line.startswith("#") and not line.startswith("source"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")

    result = subprocess.run(
        [PYTHON, str(script)] + extra_args,
        capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT)
    )
    output = result.stdout + result.stderr
    return {"ok": result.returncode == 0, "output": output}


def get_article_link() -> str:
    import re
    if not INPUT_FILE.exists():
        return ""
    for line in INPUT_FILE.read_text().splitlines():
        m = re.match(r"""article_link\s*=\s*['"]([^'"]+)['"]""", line.strip())
        if m:
            return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Routes — pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Routes — config (.input)  — structured fields
# ---------------------------------------------------------------------------

FIELD_DEFS = [
    {"key": "article_link",       "label": "Article Folder",       "type": "text",   "required": True},
    {"key": "file_name",          "label": "Manuscript File",      "type": "text",   "required": True},
    {"key": "journal_name",       "label": "Target Journal",       "type": "text",   "required": False},
    {"key": "authors",            "label": "Authors",              "type": "list",   "required": False},
    {"key": "corresponding",      "label": "Corresponding Author", "type": "text",   "required": False},
    {"key": "cover_letter_name",  "label": "Cover Letter Filename","type": "text",   "required": False},
    {"key": "title_name",         "label": "Title Filename",       "type": "text",   "required": False},
    {"key": "highlight_name",     "label": "Highlights Filename",  "type": "text",   "required": False},
]


def parse_input_fields(path: Path) -> dict:
    import re
    result = {}
    if not path.exists():
        return result
    content = path.read_text()
    # list fields: key={...} or key=[...]
    for m in re.finditer(r'(\w+)\s*=\s*[{\[](.*?)[}\]]', content, re.DOTALL):
        items = [s.strip().strip("'\"") for s in m.group(2).split(',') if s.strip().strip("'\"")]
        result[m.group(1)] = items
    # scalar fields
    for line in content.splitlines():
        m = re.match(r"""(\w+)\s*=\s*['"]([^'"]+)['"]""", line.strip())
        if m and m.group(1) not in result:
            result[m.group(1)] = m.group(2)
    return result


def write_input_fields(fields: dict) -> str:
    lines = []
    for fd in FIELD_DEFS:
        key = fd["key"]
        val = fields.get(key)
        if val is None or val == "" or val == []:
            continue
        if isinstance(val, list):
            items = ", ".join(f"'{v}'" for v in val if v.strip())
            lines.append(f"{key}={{{items}}}")
        else:
            lines.append(f"{key}='{val}'")
    return "\n".join(lines) + "\n"


@app.route("/api/config/fields", methods=["GET"])
def get_config_fields():
    data = parse_input_fields(INPUT_FILE)
    return jsonify({"fields": data, "defs": FIELD_DEFS})


@app.route("/api/config/fields", methods=["POST"])
def save_config_fields():
    fields = request.json.get("fields", {})
    INPUT_FILE.write_text(write_input_fields(fields))
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Routes — markdown files
# ---------------------------------------------------------------------------

@app.route("/api/md/<doc>", methods=["GET"])
def get_md(doc):
    fname = MD_FILES.get(doc)
    if not fname:
        return jsonify({"content": "", "exists": False})
    path = TEMP_DIR / fname
    if path.exists():
        return jsonify({"content": path.read_text(encoding="utf-8"), "exists": True})
    return jsonify({"content": "", "exists": False})


@app.route("/api/md/<doc>", methods=["POST"])
def save_md(doc):
    fname = MD_FILES.get(doc)
    if not fname:
        return jsonify({"ok": False, "error": "unknown doc"})
    TEMP_DIR.mkdir(exist_ok=True)
    path = TEMP_DIR / fname
    path.write_text(request.json.get("content", ""), encoding="utf-8")
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Routes — script execution
# ---------------------------------------------------------------------------

@app.route("/api/generate/<doc>", methods=["POST"])
def generate(doc):
    script = SCRIPTS.get(doc)
    if not script:
        return jsonify({"ok": False, "output": "Unknown document type"})
    result = run_script(script)
    return jsonify(result)


@app.route("/api/build/<doc>", methods=["POST"])
def build(doc):
    script = SCRIPTS.get(doc)
    if not script:
        return jsonify({"ok": False, "output": "Unknown document type"})
    result = run_script(script, ["--build"])
    return jsonify(result)


@app.route("/api/copy/declaration", methods=["POST"])
def copy_declaration():
    import shutil
    src = CLASSICS_DIR / "DeclarationStatement.docx"
    article_link = get_article_link()
    if not article_link:
        return jsonify({"ok": False, "output": "article_link not set in .input"})
    dst = Path(article_link) / "DeclarationStatement.docx"
    if not src.exists():
        return jsonify({"ok": False, "output": "DeclarationStatement.docx not found in CLASSICS"})
    shutil.copy2(str(src), str(dst))
    return jsonify({"ok": True, "output": f"Copied to {dst}"})


# ---------------------------------------------------------------------------
# Routes — InfoCenter / NameList
# ---------------------------------------------------------------------------

INFOCENTER_DIR  = PROJECT_ROOT / "INFOCENTER"
NAMELIST_FILE   = INFOCENTER_DIR / "NameList.json"


def _norm_person(p) -> dict:
    """Normalise a NameList entry to {name, institution, email}."""
    if isinstance(p, str):
        return {"name": p.strip(), "institution": "", "email": ""}
    return {"name": p.get("name", "").strip(),
            "institution": p.get("institution", "").strip(),
            "email": p.get("email", "").strip()}


def load_namelist() -> list[dict]:
    import json
    if not NAMELIST_FILE.exists():
        return []
    try:
        raw = json.loads(NAMELIST_FILE.read_text(encoding="utf-8"))
        return [_norm_person(p) for p in raw]
    except Exception:
        return []


def save_namelist(persons: list[dict]):
    import json
    INFOCENTER_DIR.mkdir(exist_ok=True)
    seen, result = set(), []
    for p in persons:
        p = _norm_person(p)
        if p["name"] and p["name"] not in seen:
            seen.add(p["name"])
            result.append(p)
    NAMELIST_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/api/namelist", methods=["GET"])
def get_namelist():
    return jsonify({"persons": load_namelist()})


@app.route("/api/namelist", methods=["POST"])
def update_namelist():
    """Add new persons (by name or object). Ignores duplicates."""
    new_persons = request.json.get("persons", [])
    existing = {p["name"] for p in load_namelist()}
    merged = load_namelist() + [_norm_person(p) for p in new_persons
                                if _norm_person(p)["name"] not in existing]
    save_namelist(merged)
    return jsonify({"ok": True, "persons": load_namelist()})


@app.route("/api/namelist/all", methods=["PUT"])
def replace_namelist():
    """Replace the entire list."""
    persons = request.json.get("persons", [])
    save_namelist(persons)
    return jsonify({"ok": True, "persons": load_namelist()})


@app.route("/api/docxfiles", methods=["GET"])
def list_docx_files():
    folder = request.args.get("folder", "").strip()
    if not folder:
        folder = get_article_link()
    if not folder:
        return jsonify({"files": []})
    p = Path(folder)
    if not p.exists():
        return jsonify({"files": []})
    files = sorted(f.name for f in p.iterdir() if f.suffix.lower() == ".docx")
    return jsonify({"files": files})


# ---------------------------------------------------------------------------
# Routes — output folder listing
# ---------------------------------------------------------------------------

@app.route("/api/files", methods=["GET"])
def list_files():
    article_link = get_article_link()
    if not article_link:
        return jsonify({"files": []})
    folder = Path(article_link)
    if not folder.exists():
        return jsonify({"files": []})
    files = [f.name for f in sorted(folder.iterdir()) if f.suffix in (".docx", ".pdf", ".md")]
    return jsonify({"files": files, "folder": str(folder)})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[HappyToGo STAGE] running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050)
