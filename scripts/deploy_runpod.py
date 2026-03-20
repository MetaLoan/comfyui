import os
import requests
import json
import time

def deploy():
    # 从 .env 读取 key
    env_keys = {}
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.strip().split("=", 1)
                env_keys[key] = val

    runpod_key = env_keys.get("Runpod_api_key")
    civitai_key = env_keys.get("CIVITAI_API_KEY", "")

    hf_token = env_keys.get("HF_TOKEN", "")

    if not runpod_key:
        print("❌ 未在 .env 找到 Runpod_api_key")
        return

    url = f"https://api.runpod.io/graphql?api_key={runpod_key}"
    
    query = """
    mutation PodCreate($input: PodFindAndDeployOnDemandInput!) {
        podFindAndDeployOnDemand(input: $input) {
            id
            imageName
            env
            machineId
            machine {
                podHostId
            }
        }
    }
    """
    # 为了防止 GitHub Raw DNS 污染，我们直接使用 git clone 并且设定重试机制
    start_cmd = "git clone https://github.com/MetaLoan/comfyui.git /workspace/comfyui-toolkit || (cd /workspace/comfyui-toolkit && git pull); bash /workspace/comfyui-toolkit/scripts/start_runpod.sh"
    
    variables = {
        "input": {
            "name": "ComfyUI-NSFW-Motion",
            "imageName": "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
            "gpuCount": 1,
            "volumeInGb": 100,
            "volumeMountPath": "/workspace",
            "containerDiskInGb": 30,
            "minVcpuCount": 4,
            "minMemoryInGb": 32,
            "gpuTypeId": "NVIDIA GeForce RTX 4090",
            "cloudType": "SECURE",
            "ports": "8188/http",
            "env": [
                {"key": "CIVITAI_API_KEY", "value": civitai_key},
                {"key": "HF_TOKEN", "value": hf_token}
            ],
            "dockerArgs": f"bash -c \"{start_cmd}\""
        }
    }

    print("🚀 正在向 RunPod 提交部署请求 (RTX 4090)...")
    response = requests.post(url, json={"query": query, "variables": variables})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print("❌ 部署失败，API 返回错误:")
            print(json.dumps(data['errors'], indent=2, ensure_ascii=False))
        else:
            pod_info = data['data']['podFindAndDeployOnDemand']
            if not pod_info:
                print("❌ 部署失败：未拿到资源或参数不正确。")
                print("原始返回信息:", json.dumps(data, indent=2))
                return
            pod_id = pod_info['id']
            print("==========================================")
            print("✅ 部署成功！实例已成功分配。")
            print(f"📦 Pod ID: {pod_id}")
            print("==========================================")
            print("📡 你的 ComfyUI 访问地址：")
            print(f"👉 https://{pod_id}-8188.proxy.runpod.net")
            print("==========================================")
            print("📝 注意：首次启动将执行一键脚本下载模型（约 30GB），预计需 5~10 分钟。")
            print("在此期间访问链接可能会显示 502/连接被拒，这是正常的，请耐心等待！")
    else:
        print("❌ 请求失败:", response.status_code, response.text)

if __name__ == "__main__":
    deploy()
