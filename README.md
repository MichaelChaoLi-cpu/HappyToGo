# HappyToGo

A web-based tool for generating academic manuscript submission documents — cover letter, title page, highlights, credit author statement, and declaration — powered by Google Gemini and python-docx.

---

## Features

| Document | Generator | Method |
|---|---|---|
| Cover Letter | `cover_letter_creator.py` | Gemini → Markdown → pandoc → docx |
| Title Page | `title_creator.py` | Extracts title from manuscript, applies to template |
| Highlights | `highlight_creator.py` | Gemini → 5 sentences ≤ 85 chars each |
| Credit Author Statement | `credit_author_statement_creator.py` | Web UI checkbox selection → docx |
| Declaration of Interests | from CLASSICS | Copied directly |

All document generators follow a two-step flow:

1. **Generate** — call Gemini (or read from config) → write `_temp/*.md` or `_temp/*.json`
2. **Build** — read the intermediate file (editable) → write final `.docx` to the manuscript folder

---

## Project Structure

```
HappyToGo/
├── AGENT/                        # Document generation scripts
│   ├── llm.py                    # Centralized Gemini API interface
│   ├── cover_letter_creator.py
│   ├── title_creator.py
│   ├── highlight_creator.py
│   └── credit_author_statement_creator.py
├── CLASSICS/                     # Template .docx files
│   ├── CoverLetter.docx
│   ├── Title.docx
│   ├── Highlight.docx
│   ├── CreditAuthorStatement.docx
│   └── DeclarationStatement.docx
├── STAGE/                        # Flask web UI
│   ├── app.py
│   └── templates/index.html
├── InfoCenter/                   # Author database
│   ├── NameList.example.json     # Format reference
│   └── NameList.xlsx             # (not tracked by git)
├── _temp/                        # Intermediate files (not tracked)
├── .input                        # Project config (not tracked)
├── .input.example                # Config format reference
├── .env                          # API keys (not tracked)
└── pyproject.toml
```

---

## Setup

### Requirements

- Python 3.12+
- [Conda](https://docs.conda.io/) environment (recommended)
- [pandoc](https://pandoc.org/) (for cover letter conversion)
- Google Gemini API key

### Install

```bash
# Create and activate conda environment
conda create -n HappyToGo python=3.12
conda activate HappyToGo

# Install dependencies
pip install -e .

# Install pandoc (macOS)
brew install pandoc
```

### Configuration

**1. API key** — create `.env` in the project root:

```bash
export GEMINI_API_KEY='your-key-here'
```

**2. Project config** — copy `.input.example` to `.input` and fill in:

```
article_link='/path/to/manuscript/folder'
file_name='manuscript.docx'
journal_name='Nature Human Behaviour'
authors={'First Last', 'Second Author'}
corresponding='First Last'
```

**3. Author database** — copy `InfoCenter/NameList.example.json` to `InfoCenter/NameList.json` and populate. The web UI can add and edit entries directly.

---

## Running the Web UI

```bash
./MikeWebTools/HappyToGo.sh
```

Then open [http://127.0.0.1:5050](http://127.0.0.1:5050).

### Tabs

| Tab | Purpose |
|---|---|
| **Config** | Set manuscript folder, file, journal, authors. Shows title and abstract preview after selecting a file. |
| **Title** | Generate and edit the title page. |
| **Cover Letter** | Generate and edit the cover letter. |
| **Highlights** | Generate and edit 5 highlights (≤ 85 chars each). |
| **Credit** | Assign CRediT roles to each author via checkboxes. |
| **Declaration** | Preview the declaration of interests statement. |
| **Submit** | Record journal submission date and maintain a submission log. |

---

## Running Scripts Directly

Each script can be run standalone from the project root:

```bash
# Full run (call Gemini + build docx)
python AGENT/cover_letter_creator.py
python AGENT/title_creator.py
python AGENT/highlight_creator.py

# Build only (skip Gemini, use existing _temp/ file)
python AGENT/cover_letter_creator.py --build
python AGENT/title_creator.py --build
python AGENT/highlight_creator.py --build

# Credit author statement (always reads _temp/CreditAuthorStatement.json)
python AGENT/credit_author_statement_creator.py
```

---

## Gemini Model

Defaults to `gemini-2.5-flash`. Override via environment variable:

```bash
export GEMINI_MODEL='gemini-2.0-flash'
```
