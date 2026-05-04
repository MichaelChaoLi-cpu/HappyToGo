#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_DIR/.venv"

echo ""
echo "╔══════════════════════════════════╗"
echo "║      HappyToGo  初始化           ║"
echo "╚══════════════════════════════════╝"
echo ""

# ── 1. 确保 Python 3.12 可用 ─────────────────────────────────────────────────
_ensure_python312() {
    if command -v python3.12 &>/dev/null; then
        echo "python3.12"
        return
    fi

    echo "→ 未找到 python3.12，尝试通过 Homebrew 安装..." >&2

    if ! command -v brew &>/dev/null; then
        echo "→ 未检测到 Homebrew，正在安装..." >&2
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi

    if ! command -v brew &>/dev/null; then
        echo "✗ Homebrew 安装失败，请手动安装 Python 3.12" >&2
        echo "  https://www.python.org/downloads/" >&2
        exit 1
    fi

    brew install python@3.12

    for candidate in \
        "$(brew --prefix python@3.12 2>/dev/null)/bin/python3.12" \
        /opt/homebrew/bin/python3.12 \
        /usr/local/bin/python3.12; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return
        fi
    done

    echo "✗ python3.12 安装后仍无法找到，请重开终端后重试" >&2
    exit 1
}

PYTHON_BIN=$(_ensure_python312)
PY_VER=$("$PYTHON_BIN" -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))")
echo "→ Python $PY_VER"

# ── 2. 创建虚拟环境 ───────────────────────────────────────────────────────────
NEED_VENV=true
if [ -f "$VENV_DIR/bin/python" ]; then
    VENV_VER=$("$VENV_DIR/bin/python" -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" 2>/dev/null || echo "")
    if [ "$VENV_VER" = "3.12" ]; then
        echo "→ 虚拟环境 .venv (Python 3.12) 已存在，跳过"
        NEED_VENV=false
    else
        echo "→ 虚拟环境版本为 $VENV_VER，重新创建..."
        rm -rf "$VENV_DIR"
    fi
fi

if [ "$NEED_VENV" = true ]; then
    echo "→ 创建虚拟环境 .venv..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# ── 3. 安装依赖 ───────────────────────────────────────────────────────────────
echo "→ 安装 Python 依赖（首次较慢，请稍候）..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
echo "→ 依赖安装完成"

# ── 4. 初始化 NameList（如不存在）────────────────────────────────────────────
NL_FILE="$REPO_DIR/INFOCENTER/NameList.json"
NL_EXAMPLE="$REPO_DIR/INFOCENTER/NameList.example.json"
if [ ! -f "$NL_FILE" ] && [ -f "$NL_EXAMPLE" ]; then
    cp "$NL_EXAMPLE" "$NL_FILE"
    echo "→ 已创建 INFOCENTER/NameList.json（从示例文件）"
fi

# ── 5. 确保 start.sh 可执行 ───────────────────────────────────────────────────
chmod +x "$REPO_DIR/start.sh"

# ── 6. 写入 alias 到 ~/.zshrc ─────────────────────────────────────────────────
ALIAS_CMD="alias HappyToGo='$REPO_DIR/start.sh'"
ZSHRC="$HOME/.zshrc"

if grep -q "alias HappyToGo=" "$ZSHRC" 2>/dev/null; then
    sed -i '' "s|alias HappyToGo=.*|$ALIAS_CMD|" "$ZSHRC"
    echo "→ 已更新 ~/.zshrc 中的 HappyToGo alias"
else
    {
        echo ""
        echo "# HappyToGo - https://github.com/MichaelChaoLi-cpu/HappyToGo"
        echo "$ALIAS_CMD"
    } >> "$ZSHRC"
    echo "→ 已添加 HappyToGo alias 到 ~/.zshrc"
fi

# ── 完成 ──────────────────────────────────────────────────────────────────────
echo ""
echo "✓ 初始化完成！"
echo ""
echo "  执行以下命令使 alias 立即生效："
echo ""
echo "    source ~/.zshrc"
echo ""
echo "  之后在任意终端输入："
echo ""
echo "    HappyToGo"
echo ""
echo "  即可启动，浏览器自动打开 http://localhost:5050"
echo ""
