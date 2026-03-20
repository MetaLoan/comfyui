import torch
import numpy as np
from PIL import Image
import io
import base64
import requests
import time

def tensor_to_base64_url(tensor):
    # tensor shape (1, H, W, 3)
    i = 255. * tensor.cpu().numpy().squeeze(0)
    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}"

class WanxFaceSwapNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "api_key": ("STRING", {"default": "YOUR_DASHSCOPE_API_KEY", "multiline": False}),
            "base_image": ("IMAGE",),
            "face_image": ("IMAGE",),
            "prompt": ("STRING", {"default": "Keep the main body perfectly identical, but replace the character's face completely seamlessly with the portrait provided, ensuring matching photorealistic lighting and skin texture.", "multiline": True}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("swapped_image",)
    FUNCTION = "swap_face"
    CATEGORY = "Alibaba/Wanxiang"

    def swap_face(self, api_key, base_image, face_image, prompt):
        print("[Wanx API] Preparing base64 image data...")
        base_url = tensor_to_base64_url(base_image)
        face_url = tensor_to_base64_url(face_image)
        
        endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
        payload = {
            "model": "wan2.6-image",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt},
                            {"image": face_url},
                            {"image": base_url}
                        ]
                    }
                ]
            },
            "parameters": {
                "n": 1,
                "size": "1024*1024"
            }
        }
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json; charset=utf-8",
            "X-DashScope-DataInspection": '{"input":"disable", "output":"disable"}',
            "X-DashScope-Async": "enable"
        }
        
        print("[Wanx API] Submitting task to DashScope with Unban Header...")
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"DashScope Network Error: {e} - Response: {getattr(e.response, 'text', '')}")

        resp_json = response.json()
        task_id = resp_json.get("output", {}).get("task_id")
        
        if not task_id:
            raise Exception(f"DashScope API Error (No Task ID returned): {resp_json}")
            
        print(f"[Wanx API] Task ID: {task_id}. Polling for completion...")
        poll_endpoint = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        
        poll_headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "X-DashScope-DataInspection": '{"input":"disable", "output":"disable"}'
        }

        while True:
            time.sleep(3)
            try:
                poll_resp = requests.get(poll_endpoint, headers=poll_headers)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
            except Exception as e:
                print(f"[Wanx API] Error while polling: {e}. Retrying...")
                continue

            status = poll_data.get("output", {}).get("task_status", "").upper()
            
            if status in ["SUCCEEDED", "SUCCESS"]:
                results = poll_data.get("output", {}).get("results", [])
                if not results:
                    raise Exception(f"Task succeeded but no results found: {poll_data}")
                    
                result_url = results[0].get("url")
                print(f"[Wanx API] Downloading generated image from {result_url}")
                
                try:
                    img_data = requests.get(result_url).content
                    img = Image.open(io.BytesIO(img_data)).convert("RGB")
                    np_img = np.array(img).astype(np.float32) / 255.0
                    out_tensor = torch.from_numpy(np_img).unsqueeze(0)
                    print("[Wanx API] Image successfully processed and decoded!")
                    return (out_tensor,)
                except Exception as e:
                    raise Exception(f"Failed to download or decode result image: {e}")
                
            elif status in ["FAILED", "CANCELED", "ERROR", "FAIL"]:
                err_msg = poll_data.get("message", "Unknown error")
                raise Exception(f"DashScope Task Failed: {status} - {err_msg} | Full: {poll_data}")
            else:
                print(f"    ... Status: {status} ...")


NODE_CLASS_MAPPINGS = {
    "WanxFaceSwap": WanxFaceSwapNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WanxFaceSwap": "Wanxiang API Face Editor (Anti-Ban)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
