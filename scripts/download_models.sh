#!/usr/bin/env bash
# =============================================================================
# download_models.sh — 模型下载脚本（支持 HuggingFace 和 Civitai）
# 用途：下载 Wan 2.2 NSFW 增强版主模型 + Motion LoRA
# =============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 支持外部环境变量覆盖 COMFYUI_DIR（RunPod 环境用）
COMFYUI_DIR="${COMFYUI_DIR:-$REPO_DIR/ComfyUI}"

# 自动加载 .env
if [ -f "$REPO_DIR/.env" ]; then
  export $(grep -v '^#' "$REPO_DIR/.env" | xargs)
  echo "✅ 已加载 .env 配置"
fi

echo "=========================================="
echo "  模型下载（NSFW 增强版）"
echo "=========================================="

# 检查 ComfyUI 目录
if [ ! -d "$COMFYUI_DIR" ]; then
  echo "❌ ComfyUI 目录不存在，请先运行 setup_local.sh"
  exit 1
fi

# 选择下载工具
if command -v aria2c &>/dev/null; then
  echo "✅ 使用 aria2c 多线程下载"
  DL_TOOL="aria2c"
elif command -v wget &>/dev/null; then
  echo "✅ 使用 wget 下载"
  DL_TOOL="wget"
else
  echo "✅ 使用 curl 下载"
  DL_TOOL="curl"
fi

# ---------- 通用下载函数 ----------
dl_file() {
  local url="$1"
  local output="$2"
  local description="$3"
  local auth_header="${4:-}"   # 可选：Authorization 头

  if [ -f "$output" ]; then
    local size
    size=$(du -sh "$output" | cut -f1)
    echo "✅ 已存在，跳过：$description ($size)"
    return 0
  fi

  echo "⬇️  下载：$description"
  mkdir -p "$(dirname "$output")"

  case "$DL_TOOL" in
    aria2c)
      aria2c -x 16 -s 16 -k 1M --console-log-level=error \
        ${auth_header:+--header="$auth_header"} \
        -o "$(basename "$output")" -d "$(dirname "$output")" "$url"
      ;;
    wget)
      wget -q --show-progress \
        ${auth_header:+--header="$auth_header"} \
        -O "$output" "$url"
      ;;
    curl)
      curl -L --progress-bar \
        ${auth_header:+-H "$auth_header"} \
        -o "$output" "$url"
      ;;
  esac

  echo "✅ 完成：$description"
}

# ---------- 1. 下载主模型（读取 models.txt）----------
echo ""
echo "[1/2] 下载 Wan 2.2 NSFW 增强版主模型..."

CONFIG_MODELS="$REPO_DIR/config/models.txt"

while IFS='|' read -r source name url dest || [[ -n "$source" ]]; do
  # 跳过注释和空行
  [[ "$source" =~ ^#.*$ ]] && continue
  [[ -z "$source" ]] && continue

  OUTPUT_PATH="$COMFYUI_DIR/$dest/${name}.safetensors"
  # pth 格式兼容
  if [[ "$url" == *.pth ]]; then
    OUTPUT_PATH="$COMFYUI_DIR/$dest/${name}.pth"
  fi

  case "$source" in
    hf)
      # HuggingFace 下载
      FULL_URL="https://huggingface.co/$url"
      AUTH_HEADER=""
      [ -n "$HF_TOKEN" ] && AUTH_HEADER="Authorization: Bearer $HF_TOKEN"
      dl_file "$FULL_URL" "$OUTPUT_PATH" "$name" "$AUTH_HEADER"
      ;;
    civitai)
      # Civitai 下载（Civitai 格式：civitai|name|model_id|dest）
      if [ -z "$CIVITAI_API_KEY" ]; then
        echo "⚠️  CIVITAI_API_KEY 未设置，跳过 Civitai 模型：$name"
        continue
      fi
      FULL_URL="https://civitai.com/api/download/models/${url}?token=${CIVITAI_API_KEY}"
      dl_file "$FULL_URL" "$OUTPUT_PATH" "$name"
      ;;
    *)
      echo "⚠️  未知来源 '$source'，跳过：$name"
      ;;
  esac

done < "$CONFIG_MODELS"

# ---------- 2. 下载 NSFW Motion LoRA ----------
echo ""
echo "[2/2] 下载 NSFW Motion LoRA..."

CONFIG_LORAS="$REPO_DIR/config/loras.txt"

if [ -z "$CIVITAI_API_KEY" ]; then
  echo "⚠️  CIVITAI_API_KEY 未设置，跳过所有 LoRA 下载"
  echo "   请在 .env 中配置：CIVITAI_API_KEY=your_key"
else
  while IFS='|' read -r name model_id dest_dir || [[ -n "$name" ]]; do
    [[ "$name" =~ ^#.*$ ]] && continue
    [[ -z "$name" || -z "$model_id" ]] && continue

    LORA_PATH="$COMFYUI_DIR/models/$dest_dir/${name}.safetensors"
    CIVITAI_URL="https://civitai.com/api/download/models/${model_id}?token=${CIVITAI_API_KEY}"
    dl_file "$CIVITAI_URL" "$LORA_PATH" "LoRA: $name"

  done < "$CONFIG_LORAS"
fi

# ---------- 汇总检查 ----------
echo ""
echo "========== 模型文件检查 =========="
for f in \
  "$COMFYUI_DIR/models/wan/wan2.2_i2v_480p_nsfw.safetensors" \
  "$COMFYUI_DIR/models/vae/Wan2.1_VAE.pth" \
  "$COMFYUI_DIR/models/text_encoders/clip_xlm_roberta_large.pth" \
  "$COMFYUI_DIR/models/text_encoders/umt5_xxl.pth" \
  "$COMFYUI_DIR/models/loras/nsfw_motion/doggy_slider.safetensors"; do
  if [ -f "$f" ]; then
    printf "✅ %-50s %s\n" "$(basename "$f")" "$(du -sh "$f" | cut -f1)"
  else
    printf "❌ %-50s 缺失\n" "$(basename "$f")"
  fi
done

echo ""
echo "=========================================="
echo "✅ 下载完成！"
echo "   启动命令：cd ComfyUI && python3 main.py --port 8188"
echo "=========================================="
