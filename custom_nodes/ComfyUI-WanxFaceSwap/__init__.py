import torch
import numpy as np
from PIL import Image
import io
import base64
import requests

def tensor_to_base64_url(tensor):
    # tensor shape (1, H, W, 3)
    i = 255. * tensor.cpu().numpy().squeeze(0)
    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}"

class QwenFaceSwapNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "base_image": ("IMAGE",),
            "face_image": ("IMAGE",),
            "prompt": ("STRING", {"default": "Keep the main body perfectly identical, but replace the character's face completely seamlessly with the portrait provided, ensuring matching photorealistic lighting and skin texture.", "multiline": True}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("swapped_image",)
    FUNCTION = "swap_face"
    CATEGORY = "Alibaba/Qwen"

    def swap_face(self, base_image, face_image, prompt):
        import os
        from dotenv import load_dotenv
        # Attempt to load from various potential .env locations
        load_dotenv("/workspace/ComfyUI/.env")
        load_dotenv("/Users/leo/playbox/.env") 
        
        api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise Exception("DASHSCOPE_API_KEY environment variable is not set! Please define it in your .env or system environment.")
            
        base_api_url = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1").rstrip('/')
        endpoint = f"{base_api_url}/services/aigc/multimodal-generation/generation"

        print("[Qwen API] Preparing base64 image data...")
        base_url = tensor_to_base64_url(base_image)
        face_url = tensor_to_base64_url(face_image)
        payload = {
            "model": "qwen-image-2.0-pro",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": face_url},
                            {"image": base_url},
                            {"text": prompt}
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
            "X-DashScope-DataInspection": '{"input":"disable", "output":"disable"}'
        }
        
        print("[Qwen API] Submitting synchronous task to DashScope with Unban Header...")
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"DashScope Network Error: {e} - Response: {getattr(e.response, 'text', '')}")

        resp_json = response.json()
        
        if "code" in resp_json and resp_json["code"] != "":
            raise Exception(f"DashScope API Error: {resp_json.get('code')} - {resp_json.get('message')}")
            
        output = resp_json.get("output", {})
        result_url = None
        
        # Extract from choices
        choices = output.get("choices", [])
        if choices and len(choices) > 0:
            content = choices[0].get("message", {}).get("content", [])
            for item in content:
                if item.get("type", "").lower() == "image" and item.get("image"):
                    result_url = item.get("image")
                    break
        
        # Fallback to results array
        if not result_url:
            results = output.get("results", [])
            if results and len(results) > 0:
                result_url = results[0].get("url") or results[0].get("image")
                
        if not result_url:
            raise Exception(f"Task succeeded but no image URL could be parsed from output: {resp_json}")
            
        print(f"[Qwen API] Synchronous generation complete! Downloading generated image from {result_url}")
        
        try:
            img_data = requests.get(result_url).content
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            np_img = np.array(img).astype(np.float32) / 255.0
            out_tensor = torch.from_numpy(np_img).unsqueeze(0)
            print("[Qwen API] Image successfully processed and decoded!")
            return (out_tensor,)
        except Exception as e:
            raise Exception(f"Failed to download or decode result image: {e}")

NODE_CLASS_MAPPINGS = {
    "WanxFaceSwap": QwenFaceSwapNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WanxFaceSwap": "Qwen 2.0 Pro Face Editor (Sync + Anti-Ban)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
