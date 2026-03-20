#!/usr/bin/env bash
# =============================================================================
# setup_local.sh — 本地 Mac 环境搭建脚本
# 用途：在本地 Mac 从零搭建 ComfyUI + Wan 2.2 I2V 运行环境
# =============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMFYUI_DIR="$REPO_DIR/ComfyUI"

echo "=========================================="
echo "  ComfyUI 本地环境搭建"
echo "=========================================="

# ---------- 1. 检查依赖 ----------
echo "[1/5] 检查系统依赖..."

if ! command -v python3 &>/dev/null; then
  echo "❌ 未检测到 python3，请先安装 Python 3.10+"
  exit 1
fi

PYTHON_VER=$(python3 --version | awk '{print $2}')
echo "✅ Python: $PYTHON_VER"

if ! command -v git &>/dev/null; then
  echo "❌ 未检测到 git"
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "⚠️  未检测到 ffmpeg，视频处理可能受限"
  echo "   安装命令：brew install ffmpeg"
fi

# ---------- 2. clone ComfyUI ----------
echo "[2/5] 下载 ComfyUI 主体..."

if [ -d "$COMFYUI_DIR" ]; then
  echo "✅ ComfyUI 目录已存在，跳过 clone"
  cd "$COMFYUI_DIR" && git pull
else
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

# ---------- 3. 安装 Python 依赖 ----------
echo "[3/5] 安装 Python 依赖..."

cd "$COMFYUI_DIR"

# Mac MPS（Apple Silicon）或 CPU
if python3 -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null | grep -q "True"; then
  echo "✅ 检测到 Apple Silicon MPS，使用 MPS 加速"
  pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/nightly/cpu
else
  echo "ℹ️  使用 CPU 模式（Mac 上生成速度较慢，建议 RunPod 上用 GPU）"
  pip3 install torch torchvision torchaudio
fi

pip3 install -r requirements.txt

# ---------- 4. 安装自定义节点 ----------
echo "[4/5] 安装自定义节点..."

CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

# ComfyUI Manager（必装）
if [ ! -d "$CUSTOM_NODES_DIR/ComfyUI-Manager" ]; then
  git clone https://github.com/ltdrdata/ComfyUI-Manager.git "$CUSTOM_NODES_DIR/ComfyUI-Manager"
else
  echo "✅ ComfyUI-Manager 已存在"
fi

# Wan Video Wrapper（Wan 2.2 I2V 必需）
if [ ! -d "$CUSTOM_NODES_DIR/ComfyUI-WanVideoWrapper" ]; then
  git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git "$CUSTOM_NODES_DIR/ComfyUI-WanVideoWrapper"
  pip3 install -r "$CUSTOM_NODES_DIR/ComfyUI-WanVideoWrapper/requirements.txt" 2>/dev/null || true
else
  echo "✅ ComfyUI-WanVideoWrapper 已存在"
fi

# Video Helper Suite（视频处理辅助）
if [ ! -d "$CUSTOM_NODES_DIR/ComfyUI-VideoHelperSuite" ]; then
  git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "$CUSTOM_NODES_DIR/ComfyUI-VideoHelperSuite"
  pip3 install -r "$CUSTOM_NODES_DIR/ComfyUI-VideoHelperSuite/requirements.txt" 2>/dev/null || true
else
  echo "✅ ComfyUI-VideoHelperSuite 已存在"
fi

# ---------- 5. 创建模型目录 & 软链接 ----------
echo "[5/5] 创建模型目录..."

mkdir -p "$COMFYUI_DIR/models/wan"
mkdir -p "$COMFYUI_DIR/models/vae"
mkdir -p "$COMFYUI_DIR/models/text_encoders"
mkdir -p "$COMFYUI_DIR/models/loras/nsfw_motion"
mkdir -p "$REPO_DIR/outputs"

# 将 outputs 软链到 ComfyUI 输出目录
if [ ! -L "$COMFYUI_DIR/output" ]; then
  rm -rf "$COMFYUI_DIR/output"
  ln -s "$REPO_DIR/outputs" "$COMFYUI_DIR/output"
  echo "✅ outputs 软链接已创建"
fi

echo ""
echo "=========================================="
echo "✅ 本地环境搭建完成！"
echo ""
echo "下一步："
echo "  1. 下载模型：bash scripts/download_models.sh"
echo "  2. 启动 ComfyUI：cd ComfyUI && python3 main.py --port 8188"
echo "  3. 浏览器访问：http://localhost:8188"
echo "=========================================="
