import json
import os

dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'pony_v6_reactor_faceswap.json')

workflow = {
  "last_node_id": 20,
  "last_link_id": 30,
  "nodes": [
    {
      "id": 4, "type": "CheckpointLoaderSimple", "pos": [50, 200], "size": [315, 98],
      "inputs": [],
      "outputs": [{"name": "MODEL", "type": "MODEL", "links": [1]}, {"name": "CLIP", "type": "CLIP", "links": [2, 3]}, {"name": "VAE", "type": "VAE", "links": [4]}],
      "widgets_values": ["v6_ponyDiffusionV6XL.safetensors"]
    },
    {
      "id": 5, "type": "EmptyLatentImage", "pos": [50, 400], "size": [315, 106],
      "inputs": [],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [5]}],
      "widgets_values": [832, 1216, 1] 
    },
    {
      "id": 6, "type": "CLIPTextEncode", "pos": [400, 100], "size": [400, 150], "title": "Positive Prompt",
      "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6]}],
      "widgets_values": ["score_9, score_8_up, score_7_up, realistic, masterpiece, ultra detailed, 1girl, solo, doggystyle, from behind, looking back, looking over shoulder, bent over, ass focus, deep anal penetration, penis in anus, sweat, erotic, high quality natural skin texture, realistic lighting"]
    },
    {
      "id": 7, "type": "CLIPTextEncode", "pos": [400, 300], "size": [400, 150], "title": "Negative Prompt",
      "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [7]}],
      "widgets_values": ["score_4, score_5, score_6, source_anime, cartoon, 3d, render, fake, mutated, bad anatomy, deformed anatomy, disconnected limbs, missing face, censored, mosaic, text, watermark, bad hands"]
    },
    {
      "id": 8, "type": "KSampler", "pos": [850, 200], "size": [315, 262],
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "positive", "type": "CONDITIONING", "link": 6},
        {"name": "negative", "type": "CONDITIONING", "link": 7},
        {"name": "latent_image", "type": "LATENT", "link": 5}
      ],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [8]}],
      "widgets_values": [1234567, "randomize", 30, 7.0, "euler_ancestral", "karras", 1.0]
    },
    {
      "id": 9, "type": "VAEDecode", "pos": [1200, 200], "size": [210, 46],
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": 8},
        {"name": "vae", "type": "VAE", "link": 4}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [9]}],
      "widgets_values": []
    },
    {
      "id": 10, "type": "LoadImage", "pos": [1200, 400], "size": [315, 314], "title": "User Headshot / Selfie",
      "inputs": [],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [10]}, {"name": "MASK", "type": "MASK", "links": []}],
      "widgets_values": ["selfie.jpg", "image"]
    },
    {
      "id": 11, "type": "ReActorFaceSwap", "pos": [1500, 200], "size": [315, 250],
      "inputs": [
        {"name": "input_image", "type": "IMAGE", "link": 9},
        {"name": "source_image", "type": "IMAGE", "link": 10}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [11]}],
      "widgets_values": [
        True, "inswapper_128.onnx", "retinaface_resnet50", "GFPGANv1.4", 1.0, 1.0, 
        "no", "0", "0", "gender-based", "no", "Face Parsing", 1.0
      ]
    },
    {
      "id": 12, "type": "SaveImage", "pos": [1850, 200], "size": [315, 270],
      "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
      "outputs": [],
      "widgets_values": ["pony_faceswap_output"]
    }
  ],
  "links": [
    [1, 4, 0, 8, 0, "MODEL"],
    [2, 4, 1, 6, 0, "CLIP"],
    [3, 4, 1, 7, 0, "CLIP"],
    [4, 4, 2, 9, 1, "VAE"],
    [5, 5, 0, 8, 3, "LATENT"],
    [6, 6, 0, 8, 1, "CONDITIONING"],
    [7, 7, 0, 8, 2, "CONDITIONING"],
    [8, 8, 0, 9, 0, "LATENT"],
    [9, 9, 0, 11, 0, "IMAGE"],
    [10, 10, 0, 11, 1, "IMAGE"],
    [11, 11, 0, 12, 0, "IMAGE"]
  ]
}

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, ensure_ascii=False, indent=2)

print(f"✅ Pony V6 + ReActor Workflow Generated: {dest_path}")
