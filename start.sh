#!/bin/bash
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

PYTHON="$REPO_DIR/.venv/bin/python"

# 首次运行或 venv 丢失时自动初始化
if [ ! -f "$PYTHON" ]; then
    echo "未检测到虚拟环境，正在初始化..."
    bash "$REPO_DIR/init.sh"
    source "$HOME/.zshrc" 2>/dev/null || true
fi

echo "启动 HappyToGo → http://localhost:5050"

# 延迟 1 秒后打开浏览器（等待服务器启动）
(sleep 1 && open "http://localhost:5050") &

exec "$PYTHON" "$REPO_DIR/STAGE/app.py"
