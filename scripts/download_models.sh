#!/usr/bin/env bash
# =============================================================================
# download_models.sh — 模型下载脚本
# 用途：下载 Wan 2.2 I2V 主模型 + NSFW Motion LoRA
# 需要：CIVITAI_API_KEY 环境变量（用于下载 LoRA）
# =============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMFYUI_DIR="$REPO_DIR/ComfyUI"

echo "=========================================="
echo "  模型下载"
echo "=========================================="

# 检查 ComfyUI 目录
if [ ! -d "$COMFYUI_DIR" ]; then
  echo "❌ ComfyUI 目录不存在，请先运行 setup_local.sh"
  exit 1
fi

# 检查下载工具
if command -v aria2c &>/dev/null; then
  DOWNLOADER="aria2c"
  echo "✅ 使用 aria2c 多线程下载"
elif command -v wget &>/dev/null; then
  DOWNLOADER="wget"
  echo "✅ 使用 wget 下载"
else
  DOWNLOADER="curl"
  echo "✅ 使用 curl 下载"
fi

# 通用下载函数
download_file() {
  local url="$1"
  local output="$2"
  local description="$3"

  if [ -f "$output" ]; then
    echo "✅ 已存在，跳过：$description"
    return 0
  fi

  echo "⬇️  下载中：$description"
  mkdir -p "$(dirname "$output")"

  if [ "$DOWNLOADER" = "aria2c" ]; then
    aria2c -x 8 -s 8 -k 1M -o "$(basename "$output")" -d "$(dirname "$output")" "$url"
  elif [ "$DOWNLOADER" = "wget" ]; then
    wget -q --show-progress -O "$output" "$url"
  else
    curl -L --progress-bar -o "$output" "$url"
  fi

  echo "✅ 下载完成：$description"
}

# ---------- 1. 下载 Wan 2.2 I2V 主模型 ----------
echo ""
echo "[1/3] 下载 Wan 2.2 I2V 主模型..."
echo "⚠️  文件较大（~14GB 以上），请确保网络稳定和磁盘空间充足"

# Wan 2.2 480p I2V 模型（较小，适合测试）
download_file \
  "https://huggingface.co/Wan-AI/Wan2.2-I2V-14B/resolve/main/wan2.2_i2v_14B_480p.safetensors" \
  "$COMFYUI_DIR/models/wan/wan2.2_i2v_14B_480p.safetensors" \
  "Wan2.2 I2V 14B 480p"

# VAE
download_file \
  "https://huggingface.co/Wan-AI/Wan2.2-I2V-14B/resolve/main/Wan2.2_VAE.safetensors" \
  "$COMFYUI_DIR/models/vae/Wan2.2_VAE.safetensors" \
  "Wan2.2 VAE"

# Text Encoders
download_file \
  "https://huggingface.co/Wan-AI/Wan2.2-I2V-14B/resolve/main/models_clip_open-clip-xlm-roberta-large-vit-huge-14.pth" \
  "$COMFYUI_DIR/models/text_encoders/clip_xlm_roberta_large.pth" \
  "CLIP Text Encoder"

download_file \
  "https://huggingface.co/Wan-AI/Wan2.2-I2V-14B/resolve/main/models_t5_umt5-xxl-enc-bf16.pth" \
  "$COMFYUI_DIR/models/text_encoders/umt5_xxl.pth" \
  "T5 Text Encoder"

# ---------- 2. 下载 NSFW Motion LoRA ----------
echo ""
echo "[2/3] 下载 NSFW Motion LoRA..."

if [ -z "$CIVITAI_API_KEY" ]; then
  echo "⚠️  未设置 CIVITAI_API_KEY，跳过 LoRA 下载"
  echo "   手动设置方式：export CIVITAI_API_KEY=your_key_here"
else
  CONFIG_FILE="$REPO_DIR/config/loras.txt"

  while IFS='|' read -r name model_id dest_dir || [[ -n "$name" ]]; do
    # 跳过注释和空行
    [[ "$name" =~ ^#.*$ ]] && continue
    [[ -z "$name" ]] && continue

    DEST_PATH="$COMFYUI_DIR/models/$dest_dir/${name}.safetensors"

    if [ -f "$DEST_PATH" ]; then
      echo "✅ 已存在，跳过：$name"
      continue
    fi

    echo "⬇️  下载 LoRA：$name (Civitai ID: $model_id)"
    mkdir -p "$COMFYUI_DIR/models/$dest_dir"

    CIVITAI_URL="https://civitai.com/api/download/models/${model_id}?token=${CIVITAI_API_KEY}"

    if [ "$DOWNLOADER" = "aria2c" ]; then
      aria2c -x 4 -s 4 -o "${name}.safetensors" -d "$COMFYUI_DIR/models/$dest_dir" "$CIVITAI_URL"
    elif [ "$DOWNLOADER" = "wget" ]; then
      wget -q --show-progress -O "$DEST_PATH" "$CIVITAI_URL"
    else
      curl -L --progress-bar -o "$DEST_PATH" "$CIVITAI_URL"
    fi

    echo "✅ LoRA 下载完成：$name"
  done < "$CONFIG_FILE"
fi

# ---------- 3. 检查完整性 ----------
echo ""
echo "[3/3] 检查模型文件..."

check_file() {
  local path="$1"
  local name="$2"
  if [ -f "$path" ]; then
    SIZE=$(du -sh "$path" | cut -f1)
    echo "✅ $name ($SIZE)"
  else
    echo "❌ 缺失：$name"
  fi
}

check_file "$COMFYUI_DIR/models/wan/wan2.2_i2v_14B_480p.safetensors" "Wan2.2 I2V 主模型"
check_file "$COMFYUI_DIR/models/vae/Wan2.2_VAE.safetensors" "VAE"
check_file "$COMFYUI_DIR/models/text_encoders/clip_xlm_roberta_large.pth" "CLIP Encoder"
check_file "$COMFYUI_DIR/models/text_encoders/umt5_xxl.pth" "T5 Encoder"

echo ""
echo "=========================================="
echo "✅ 模型下载任务完成！"
echo ""
echo "下一步："
echo "  cd ComfyUI && python3 main.py --port 8188"
echo "=========================================="
