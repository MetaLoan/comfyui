#!/usr/bin/env bash
# =============================================================================
# start_runpod.sh — RunPod 一键部署脚本
# 用途：在全新 RunPod 实例上自动完成 ComfyUI 环境搭建并启动服务
#
# 使用方式（在 RunPod Terminal 中执行）：
#   curl -fsSL https://raw.githubusercontent.com/MetaLoan/comfyui/main/scripts/start_runpod.sh | bash
#
# 可选环境变量：
#   CIVITAI_API_KEY   — Civitai API Key（下载 LoRA 必填）
#   HF_TOKEN          — Hugging Face Token（可选）
#   SKIP_MODELS       — 设为 1 则跳过模型下载（调试用）
#   COMFYUI_PORT      — ComfyUI 监听端口（默认 8188）
# =============================================================================
set -e

# ---------- 配置 ----------
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
WORKSPACE="/workspace"
COMFYUI_DIR="$WORKSPACE/ComfyUI"
TOOLKIT_DIR="$WORKSPACE/comfyui-toolkit"

echo "============================================================"
echo "  ComfyUI NSFW Motion LoRA Toolkit — RunPod 一键部署"
echo "============================================================"
echo "  时间: $(date)"
echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "  VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "============================================================"

# ---------- 1. 系统依赖 ----------
echo ""
echo "[1/6] 安装系统依赖..."

apt-get update -qq
apt-get install -y -qq \
  git wget curl aria2 ffmpeg \
  libgl1-mesa-glx libglib2.0-0 \
  python3-pip python3-venv \
  > /dev/null 2>&1

echo "✅ 系统依赖安装完成"

# ---------- 2. clone 本仓库 ----------
echo ""
echo "[2/6] 获取工具包..."

if [ -d "$TOOLKIT_DIR" ]; then
  echo "✅ 工具包已存在，更新中..."
  cd "$TOOLKIT_DIR" && git pull
else
  git clone https://github.com/MetaLoan/comfyui.git "$TOOLKIT_DIR"
fi

echo "✅ 工具包就绪"

# ---------- 3. clone & 配置 ComfyUI ----------
echo ""
echo "[3/6] 配置 ComfyUI..."

if [ -d "$COMFYUI_DIR" ]; then
  echo "✅ ComfyUI 已存在，更新中..."
  cd "$COMFYUI_DIR" && git pull
else
  git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

cd "$COMFYUI_DIR"

# 安装 Python 依赖（RunPod 已有 CUDA PyTorch）
pip install -q -r requirements.txt

# 创建模型目录
mkdir -p models/wan models/vae models/text_encoders models/loras/nsfw_motion

# 输出目录
mkdir -p "$WORKSPACE/outputs"
[ -L "$COMFYUI_DIR/output" ] || { rm -rf "$COMFYUI_DIR/output"; ln -s "$WORKSPACE/outputs" "$COMFYUI_DIR/output"; }

# ---------- 4. 安装自定义节点 ----------
echo ""
echo "[4/6] 安装自定义节点..."

CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
mkdir -p "$CUSTOM_NODES_DIR"

install_node() {
  local name="$1"
  local url="$2"
  local req_file="$3"

  if [ -d "$CUSTOM_NODES_DIR/$name" ]; then
    echo "✅ $name 已存在，跳过"
    return
  fi

  echo "⬇️  安装 $name..."
  git clone "$url" "$CUSTOM_NODES_DIR/$name"

  if [ -n "$req_file" ] && [ -f "$CUSTOM_NODES_DIR/$name/$req_file" ]; then
    pip install -q -r "$CUSTOM_NODES_DIR/$name/$req_file" 2>/dev/null || true
  fi

  echo "✅ $name 安装完成"
}

install_node "ComfyUI-Manager" \
  "https://github.com/ltdrdata/ComfyUI-Manager.git" \
  "requirements.txt"

install_node "ComfyUI-WanVideoWrapper" \
  "https://github.com/kijai/ComfyUI-WanVideoWrapper.git" \
  "requirements.txt"

install_node "ComfyUI-VideoHelperSuite" \
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" \
  "requirements.txt"

install_node "ComfyUI-KJNodes" \
  "https://github.com/kijai/ComfyUI-KJNodes.git" \
  "requirements.txt"

# ---------- 5. 下载模型 ----------
echo ""
echo "[6/6] 下载模型..."

if [ "${SKIP_MODELS:-0}" = "1" ]; then
  echo "⚠️  SKIP_MODELS=1，跳过模型下载（调试模式）"
else
  # 直接调用统一下载脚本
  bash "$TOOLKIT_DIR/scripts/download_models.sh"
fi

# ---------- 6. 启动 ComfyUI ----------
echo ""
echo "[6/6] 启动 ComfyUI..."

# 复制工作流到 ComfyUI
mkdir -p "$COMFYUI_DIR/user/default/workflows"
cp -f "$TOOLKIT_DIR/workflows/"*.json "$COMFYUI_DIR/user/default/workflows/" 2>/dev/null || true

cd "$COMFYUI_DIR"

echo ""
echo "============================================================"
echo "✅ 部署完成！ComfyUI 正在启动..."
echo "   访问地址：http://0.0.0.0:${COMFYUI_PORT}"
echo "   （RunPod 中点击 Connect → HTTP Service → 8188）"
echo "============================================================"
echo ""

# 启动 ComfyUI（前台运行，保持 RunPod 实例活跃）
python3 main.py \
  --listen 0.0.0.0 \
  --port "$COMFYUI_PORT" \
  --enable-cors-header \
  --preview-method auto
