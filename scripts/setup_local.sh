#!/usr/bin/env bash
# =============================================================================
# setup_local.sh — 本地 Mac 环境搭建脚本（使用 venv 虚拟环境）
# =============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMFYUI_DIR="$REPO_DIR/ComfyUI"
VENV_DIR="$REPO_DIR/comfyui_venv"

echo "=========================================="
echo "  ComfyUI 本地环境搭建"
echo "=========================================="

# ---------- 1. 检查依赖 ----------
echo "[1/6] 检查系统依赖..."

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
  echo "⚠️  未检测到 ffmpeg（可选）：brew install ffmpeg"
fi

# ---------- 2. clone or update ComfyUI ----------
echo "[2/6] 下载 ComfyUI 主体..."

if [ -d "$COMFYUI_DIR" ]; then
  echo "✅ ComfyUI 目录已存在，更新中..."
  cd "$COMFYUI_DIR" && git pull
else
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

# ---------- 3. 创建虚拟环境 ----------
echo "[3/6] 创建 Python 虚拟环境..."

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  echo "✅ 虚拟环境已创建：$VENV_DIR"
else
  echo "✅ 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
echo "✅ 已激活虚拟环境"

# ---------- 4. 安装 Python 依赖 ----------
echo "[4/6] 安装 Python 依赖..."

pip install --upgrade pip -q

# Mac Apple Silicon MPS 加速
if python3 -c "import platform; exit(0 if platform.processor() == 'arm' else 1)" 2>/dev/null; then
  echo "✅ 检测到 Apple Silicon，安装 MPS 版 PyTorch"
  pip install torch torchvision torchaudio -q
else
  echo "ℹ️  Intel Mac / CPU 模式"
  pip install torch torchvision torchaudio -q
fi

pip install -r "$COMFYUI_DIR/requirements.txt" -q
echo "✅ Python 依赖安装完成"

# ---------- 5. 安装自定义节点 ----------
echo "[5/6] 安装自定义节点..."

CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

install_node() {
  local name="$1"
  local url="$2"
  local req="$3"

  if [ -d "$CUSTOM_NODES_DIR/$name" ]; then
    echo "✅ $name 已存在"
    return
  fi

  echo "⬇️  安装 $name..."
  git clone "$url" "$CUSTOM_NODES_DIR/$name"
  if [ -n "$req" ] && [ -f "$CUSTOM_NODES_DIR/$name/$req" ]; then
    pip install -r "$CUSTOM_NODES_DIR/$name/$req" -q 2>/dev/null || true
  fi
  echo "✅ $name 安装完成"
}

install_node "ComfyUI-Manager" \
  "https://github.com/ltdrdata/ComfyUI-Manager.git" "requirements.txt"

install_node "ComfyUI-WanVideoWrapper" \
  "https://github.com/kijai/ComfyUI-WanVideoWrapper.git" "requirements.txt"

install_node "ComfyUI-VideoHelperSuite" \
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "requirements.txt"

install_node "ComfyUI-KJNodes" \
  "https://github.com/kijai/ComfyUI-KJNodes.git" "requirements.txt"

# ---------- 6. 目录 & 软链接 ----------
echo "[6/6] 创建模型目录..."

mkdir -p "$COMFYUI_DIR/models/wan"
mkdir -p "$COMFYUI_DIR/models/vae"
mkdir -p "$COMFYUI_DIR/models/text_encoders"
mkdir -p "$COMFYUI_DIR/models/loras/nsfw_motion"
mkdir -p "$REPO_DIR/outputs"

if [ ! -L "$COMFYUI_DIR/output" ]; then
  rm -rf "$COMFYUI_DIR/output"
  ln -s "$REPO_DIR/outputs" "$COMFYUI_DIR/output"
  echo "✅ outputs 软链接已创建"
fi

# 复制工作流
mkdir -p "$COMFYUI_DIR/user/default/workflows"
cp -f "$REPO_DIR/workflows/"*.json "$COMFYUI_DIR/user/default/workflows/" 2>/dev/null && \
  echo "✅ 工作流已复制到 ComfyUI" || true

echo ""
echo "=========================================="
echo "✅ 本地环境搭建完成！"
echo ""
echo "启动 ComfyUI："
echo "  source comfyui_venv/bin/activate"
echo "  cd ComfyUI && python main.py --port 8188"
echo ""
echo "或者直接运行快捷命令："
echo "  bash scripts/start_local.sh"
echo "=========================================="
