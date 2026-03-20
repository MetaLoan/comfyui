import os
import runpod

def check_status(pod_id):
    # 从 .env 读取 key
    env_keys = {}
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.strip().split("=", 1)
                env_keys[key] = val

    runpod_key = env_keys.get("Runpod_api_key")
    if not runpod_key:
        print("❌ 未在 .env 找到 Runpod_api_key")
        return

    runpod.api_key = runpod_key

    print(f"🔍 正在查询 Pod {pod_id} 状态...")
    try:
        # Get pod info
        pod = runpod.get_pod(pod_id)
        print("==========================================")
        print(f"✅ Pod Id: {pod['id']}")
        print(f"📦 Image: {pod['imageName']}")
        print(f"🖥️  Machine Id: {pod['machineId']}")
        print("==========================================")
        
    except Exception as e:
        print("❌ 查询失败:", str(e))

if __name__ == "__main__":
    check_status("0n370txi9baxf2")
