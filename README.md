# ComfyUI NSFW Motion LoRA Toolkit

可复用的 NSFW 动作 LoRA 工作流套件，基于 Wan 2.2 I2V。
只需替换参考图，即可生成相同动作的写实视频。

## 项目结构

```
comfyui/
├── workflows/          # ComfyUI 工作流 JSON（拖入界面即可加载）
├── scripts/            # 环境搭建 & 部署脚本
├── config/             # 模型和 LoRA 下载列表
└── outputs/            # 生成视频输出（git 忽略）
```

## 快速开始

### 本地 Mac 测试

```bash
# 1. 搭建环境（首次运行）
bash scripts/setup_local.sh

# 2. 下载模型
export CIVITAI_API_KEY=your_key_here
bash scripts/download_models.sh

# 3. 启动 ComfyUI
cd ComfyUI && python main.py --port 8188
# 浏览器访问 http://localhost:8188
```

### RunPod 一键部署

在 RunPod 实例的 Terminal 中执行：

```bash
curl -fsSL https://raw.githubusercontent.com/MetaLoan/comfyui/main/scripts/start_runpod.sh | bash
```

## 工作流说明

| 文件 | 用途 |
|------|------|
| `wan2.2_i2v_base.json` | Wan 2.2 I2V 基础工作流 |
| `wan2.2_i2v_nsfw_lora.json` | 叠加 NSFW Doggy Slider LoRA 的完整工作流 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `CIVITAI_API_KEY` | Civitai API Key，用于下载 LoRA |
| `HF_TOKEN` | Hugging Face Token（可选，用于私有模型） |

## 所需硬件

| 环境 | 最低要求 |
|------|----------|
| 本地 | VRAM 16GB+（RTX 4090 推荐），存储 50GB+ |
| RunPod | GPU: RTX 4090 / A100，存储 100GB+ |
