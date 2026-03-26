# Changelog

All notable changes to HappyToGo will be documented in this file.

---

## [0.0.1] - 2026-03-22

### Added
- Cover letter generator powered by Gemini LLM (`cover_letter_creator.py`)
- Title page creator (`title_page_creator.py`)
- Declaration statement creator
- Highlight creator
- Credit author statement support
- Web UI stage for running all generators (`STAGE/app.py`)

### Fixed
- Cover letter revision and formatting
- Author name list update
- Abstract display in title page

### Docs
- Completed environment setup guide and README

---

## [0.0.2] - 2026-03-26

### Changed
- Cover letter output now saved into a subdirectory named after the target journal
- Signature block in cover letter now uses blank lines between each line for proper left-aligned formatting
