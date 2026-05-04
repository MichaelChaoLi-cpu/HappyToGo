# HappyToGo

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Stars](https://img.shields.io/github/stars/MichaelChaoLi-cpu/HappyToGo?style=social)

A web-based tool for generating academic manuscript submission documents — cover letter, title page, highlights, credit author statement, and declaration of interests — powered by Gemini or DeepSeek AI and python-docx.

> [中文说明](#中文说明) | English

---

## Quick Start

**Requires: macOS, Python 3.12 recommended**

```bash
git clone https://github.com/MichaelChaoLi-cpu/HappyToGo.git
cd HappyToGo
./init.sh
source ~/.zshrc
```

Then type `HappyToGo` in any terminal to launch. The browser opens automatically at `http://localhost:5050`.

**First use**: click ⚙️ SETTINGS in the sidebar, select your LLM provider (Gemini or DeepSeek), and paste your API key.

---

## Features

| Document | How it works |
|---|---|
| **Cover Letter** | LLM generates content → editable Markdown → python-docx |
| **Title Page** | Extracts title from manuscript, authors & affiliations from NameList |
| **Highlights** | LLM generates 5 sentences ≤ 85 chars each |
| **Credit Author Statement** | Checkbox UI → author–role mapping → docx |
| **Declaration of Interests** | One-click generate (hardcoded template) |

All generators follow a two-step flow:
1. **Generate** — call LLM → write `_temp/*.md` or `_temp/*.json` (editable)
2. **Build DOCX** — read the intermediate file → write final `.docx` to the manuscript folder

---

## Project Structure

```
HappyToGo/
├── AGENT/                        # Document generation scripts
│   ├── llm.py                    # Gemini / DeepSeek unified interface
│   ├── cover_letter_creator.py
│   ├── title_creator.py
│   ├── highlight_creator.py
│   └── credit_author_statement_creator.py
├── STAGE/                        # Flask web UI
│   ├── app.py
│   └── templates/index.html
├── INFOCENTER/                   # Author database
│   ├── NameList.example.json
│   └── NameList.json             # (auto-created from example, not tracked)
├── _temp/                        # Intermediate files (not tracked)
├── .input                        # Project config (not tracked)
├── .input.example                # Config format reference
├── .env                          # API keys (not tracked, managed via UI)
├── init.sh                       # One-time setup
├── start.sh                      # Launch script
└── pyproject.toml
```

---

## LLM Providers

| Provider | Model | Key variable |
|---|---|---|
| Gemini (default) | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` |

Switch providers in the ⚙️ SETTINGS panel — no config file editing needed.

---

## Tabs

| Tab | Purpose |
|---|---|
| **Config** | Manuscript folder, file, journal, authors. Shows title & abstract preview. |
| **Title** | Generate and edit the title page. |
| **Cover Letter** | Generate and edit the cover letter. |
| **Highlights** | Generate and edit 5 highlights (≤ 85 chars each). |
| **Credit** | Assign CRediT roles per author via checkboxes. |
| **Declaration** | Generate declaration of interests. |
| **Submit** | Record submission dates and maintain a submission log. |

---

## Version History

### v0.1.0 (2026-05)
- All document formats hardcoded in python-docx (no template files needed)
- DeepSeek support via OpenAI-compatible API
- NameList extended with position, phone, address fields
- Affiliations and corresponding author contact auto-derived from NameList
- LLM provider selector in Settings modal

### v0.0.2 (2026-04)
- Initial public release

---

## License

[MIT](LICENSE) © 2026 MichaelChaoLi-cpu

---

---

# 中文说明

![Version](https://img.shields.io/badge/版本-0.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/许可证-MIT-green)
![Platform](https://img.shields.io/badge/平台-macOS-lightgrey)

学术论文投稿文件生成工具。通过 Web 界面一键生成投稿信、标题页、研究亮点、作者贡献声明和利益冲突声明，支持 Gemini 和 DeepSeek 双模型。

---

## 快速开始

**前提：macOS，推荐 Python 3.12**

```bash
git clone https://github.com/MichaelChaoLi-cpu/HappyToGo.git
cd HappyToGo
./init.sh
source ~/.zshrc
```

之后在任意终端输入 `HappyToGo` 即可启动，浏览器自动打开 `http://localhost:5050`。

**首次使用**：点击左侧边栏底部 ⚙️ SETTINGS，选择 LLM 提供商（Gemini 或 DeepSeek），粘贴 API Key 保存。

---

## 功能

| 文档 | 生成方式 |
|---|---|
| **投稿信** | AI 生成内容 → 可编辑 Markdown → python-docx |
| **标题页** | 从稿件提取标题，从 NameList 读取作者和机构信息 |
| **研究亮点** | AI 生成 5 条 ≤ 85 字符的亮点句 |
| **作者贡献声明** | 勾选界面分配 CRediT 角色 → 生成 docx |
| **利益冲突声明** | 一键生成（格式固化在程序中） |

---

## LLM 支持

| 提供商 | 默认模型 | 密钥变量 |
|---|---|---|
| Gemini（默认） | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` |

在 ⚙️ SETTINGS 面板中切换，无需手动修改配置文件。

---

## 许可证

[MIT](LICENSE) © 2026 MichaelChaoLi-cpu
