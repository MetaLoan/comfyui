#!/usr/bin/env bash
# =============================================================================
# start_local.sh — 本地快捷启动脚本
# 自动激活 venv 并启动 ComfyUI
# =============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_DIR/comfyui_venv"
COMFYUI_DIR="$REPO_DIR/ComfyUI"

if [ ! -d "$VENV_DIR" ]; then
  echo "❌ 虚拟环境不存在，请先运行：bash scripts/setup_local.sh"
  exit 1
fi

# 加载 .env
if [ -f "$REPO_DIR/.env" ]; then
  export $(grep -v '^#' "$REPO_DIR/.env" | xargs)
fi

source "$VENV_DIR/bin/activate"
echo "✅ 已激活虚拟环境"

cd "$COMFYUI_DIR"
echo "🚀 启动 ComfyUI..."
echo "   访问地址：http://localhost:8188"
echo ""
python main.py --port 8188
