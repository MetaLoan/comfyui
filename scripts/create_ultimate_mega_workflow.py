import json
import os
import copy

source_path = "/tmp/Rapid-AIO-Mega.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'ultimate_aio_pony_wan_video.json')

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Modify basic Wan video nodes based on v16 logic
for node in data["nodes"]:
    node["mode"] = 0
    if node["type"] == "CheckpointLoaderSimple":
        node["widgets_values"][0] = "wan/Wan2_1-I2V-14B-nsfw.safetensors"
    elif node["type"] == "WanVideoVACEStartToEndFrame":
        for inp in node.get("inputs", []):
            if inp.get("name") == "end_image":
                link_id_to_remove = inp.get("link")
                if link_id_to_remove is not None:
                    data["links"] = [l for l in data["links"] if l[0] != link_id_to_remove]
                inp["link"] = None
    elif node["type"] == "WanVaceToVideo":
        node["widgets_values"][0] = 832
        node["widgets_values"][1] = 480
    elif node["type"] == "KSampler":
        node["widgets_values"][2] = 20
        node["widgets_values"][4] = "euler"
        node["widgets_values"][5] = "beta"
    elif node["type"] == "PrimitiveInt" and node["id"] == 48:
        node["widgets_values"][0] = 17 # Drop frames severely from 49 to 17 to survive FP8 upcasting overhead
    elif node["type"] == "CLIPTextEncode":
        if node["id"] == 9:
            base = "(exact same woman as reference:1.65), (identical facial identity:1.6), (preserve original face exactly throughout:1.55), (consistent character identity all frames:1.5), (no face loss no disappearance:1.45), detailed original face natural skin as input, "
            action = "woman in doggystyle three-quarter side view OR profile side angle, BOTH face looking back over shoulder AND ass pussy anus fully visible in frame, head turned back eyes visible mouth moaning pleasure expression, face stays in frame entire video, no pure rear view no full from_behind no face cropped no face out of frame, ass up high presenting tight anus and wet pussy from side, erect penis thrusting deep into anus from behind, deep anal penetration, penis sliding in and out of asshole rhythmically, anus gripping stretching around shaft, lube glistening on anus penis, pussy lips parted dripping arousal untouched, ass cheeks jiggling rippling with each thrust, breasts hanging swaying, smooth gradual thrusting motion slow build to faster, static three-quarter side camera OR eye-level side angle keeping face and ass in composition, high detail realistic skin sweat lube shadows, consistent identity stable facial features no jump no sudden perspective change, erotic intense expression"
            node["widgets_values"][0] = base + action
        elif node["id"] == 10:
            node["widgets_values"][0] = "pure rear view, full from_behind, ass_focus only, anus_focus only, face disappears, face not visible after start, face out of frame, head cut off, sudden jump to back angle, perspective shift, flash cut to rear, no face in frame, face missing, discontinuous motion, LoRA overbias ass only, different person, identity change, identity drift, face reconstruction, face morphing, beautified face, generic face, altered facial features, race change, ethnicity change, different ethnicity, any skin tone change, eye shape change, nose change, lip change, asymmetrical face, distorted face, deformed eyes, deformed mouth, extra teeth, bad anatomy, mutated face, off-model face, wrong facial structure, blurry face, low detail face, overexposed skin, unnatural skin, artifacts on face, motion blur on face, closed mouth the whole time, no saliva, no penis, censored, mosaic, text, watermark, ugly, poorly drawn face, extra limbs, bad proportions, grainy, flickering face, frozen expression"

# Filter out old links: Link 161 (LoadImage->VACE) and Link 150 (CheckpointLoader->ModelSamplingSD3)
data["links"] = [l for l in data["links"] if l[0] not in [161, 150]]

# Determine maximum Node ID so we don't collide
max_id = max([n["id"] for n in data["nodes"]])

# Start appending Pony Nodes
# Make IDs strictly huge to avoid any collision
P_CKPT = max_id + 500
P_LATENT = max_id + 501
P_CLIP_POS = max_id + 502
P_CLIP_NEG = max_id + 503
P_KSAMPLER = max_id + 504
P_VAE_DEC = max_id + 505
P_SELFIE = max_id + 506
P_QWEN = max_id + 507

IMG_SCALE = max_id + 100
FACE_LOAD = max_id + 201
FACE_APPLY = max_id + 200
LORA_LOAD = max_id + 300

pony_nodes = [
    {
      "id": P_CKPT, "type": "CheckpointLoaderSimple", "pos": [-1000, -800], "size": [315, 98], "mode": 0,
      "inputs": [],
      "outputs": [{"name": "MODEL", "type": "MODEL", "links": []}, {"name": "CLIP", "type": "CLIP", "links": []}, {"name": "VAE", "type": "VAE", "links": []}],
      "widgets_values": ["CyberRealistic_Pony_v17.safetensors"]
    },
    {
      "id": P_LATENT, "type": "EmptyLatentImage", "pos": [-1000, -600], "size": [315, 106], "mode": 0,
      "inputs": [],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": []}],
      "widgets_values": [832, 1216, 1] 
    },
    {
      "id": P_CLIP_POS, "type": "CLIPTextEncode", "pos": [-600, -900], "size": [400, 150], "title": "Pony Positive", "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": None}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}],
      "widgets_values": ["source_real, RAW photo, highly detailed, photorealistic, 8k uhd, dslr, soft lighting, skin texture, natural skin, score_9, score_8_up, score_7_up, realistic, masterpiece, ultra detailed, 1girl, solo, doggystyle, from behind, looking back, looking over shoulder, bent over, ass focus, deep anal penetration, penis in anus, sweat, erotic, high quality natural skin texture, realistic lighting"]
    },
    {
      "id": P_CLIP_NEG, "type": "CLIPTextEncode", "pos": [-600, -700], "size": [400, 150], "title": "Pony Negative", "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": None}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}],
      "widgets_values": ["source_anime, source_cartoon, source_pony, 3d, render, sketch, painting, illustration, drawing, plastic, score_4, score_5, score_6, cartoon, fake, mutated, bad anatomy, deformed anatomy, disconnected limbs, missing face, censored, mosaic, text, watermark, bad hands"]
    },
    {
      "id": P_KSAMPLER, "type": "KSampler", "pos": [-150, -800], "size": [315, 262], "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": None},
        {"name": "positive", "type": "CONDITIONING", "link": None},
        {"name": "negative", "type": "CONDITIONING", "link": None},
        {"name": "latent_image", "type": "LATENT", "link": None}
      ],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": []}],
      "widgets_values": [1234567, "randomize", 30, 7.0, "euler_ancestral", "karras", 1.0]
    },
    {
      "id": P_VAE_DEC, "type": "VAEDecode", "pos": [200, -800], "size": [210, 46], "mode": 0,
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": None},
        {"name": "vae", "type": "VAE", "link": None}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
      "widgets_values": []
    },
    {
      "id": P_SELFIE, "type": "LoadImage", "pos": [200, -600], "size": [315, 314], "title": "User Headshot / Selfie", "mode": 0,
      "inputs": [],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}, {"name": "MASK", "type": "MASK", "links": []}],
      "widgets_values": ["selfie.jpg", "image"]
    },
    {
      "id": P_QWEN, "type": "WanxFaceSwap", "pos": [600, -800], "size": [315, 200], "mode": 0,
      "inputs": [
        {"name": "base_image", "type": "IMAGE", "link": None},
        {"name": "face_image", "type": "IMAGE", "link": None}
      ],
      "outputs": [{"name": "swapped_image", "type": "IMAGE", "links": []}],
      "widgets_values": [
        "使用给定的人物肖像提取头像放入给定的性爱场景图中进行替换输出新的性爱场景，输出图片要求：人物姿势自然享受，角度合理舒展，人物主体完整没有裁切，头部的角度符合原图的角度包括侧脸角度要正常，肤色体格重绘制要符合上传头像的的人种。同时头身比例调整到协调状态"
      ]
    }
]

# ImageScale and StandIn and LoRA
v16_nodes = [
    {
      "id": IMG_SCALE, "type": "ImageScale", "pos": [1000, -800], "size": [270, 130], "flags": {}, "order": 1, "mode": 0,
      "inputs": [{"name": "image", "type": "IMAGE", "link": None}], # Link will come from P_QWEN
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}],
      "properties": {"Node name for S&R": "ImageScale"}, "widgets_values": ["nearest-exact", 832, 480, "disabled"]
    },
    {
      "id": FACE_LOAD, "type": "FaceProcessorLoader", "pos": [1000, -500], "size": [315, 60], "flags": {}, "order": 1, "mode": 0,
      "inputs": [],
      "outputs": [{"name": "face_processor", "type": "FACE_PROCESSOR", "links": []}],
      "properties": {"Node name for S&R": "FaceProcessorLoader"}, "widgets_values": ["model.pt"]
    },
    {
      "id": FACE_APPLY, "type": "ApplyFaceProcessor", "pos": [1350, -800], "size": [315, 200], "flags": {}, "order": 2, "mode": 0,
      "inputs": [{"name": "face_processor", "type": "FACE_PROCESSOR", "link": None}, {"name": "image", "type": "IMAGE", "link": None}],
      "outputs": [{"name": "processed_image", "type": "IMAGE", "links": []}, {"name": "face_rgba", "type": "IMAGE", "links": []}],
      "properties": {"Node name for S&R": "ApplyFaceProcessor"}, "widgets_values": [512, 10, 1.35, 0.45, True, False]
    },
    {
      "id": LORA_LOAD, "type": "LoraLoaderModelOnly", "pos": [1350, -500], "size": [315, 120], "flags": {}, "order": 3, "mode": 0,
      "inputs": [{"name": "model", "type": "MODEL", "link": None}],
      "outputs": [{"name": "MODEL", "type": "MODEL", "links": []}],
      "properties": {"Node name for S&R": "LoraLoaderModelOnly"}, 
      "widgets_values": ["wan22_i2v_anal_v1_high_noise.safetensors", 0.75]
    }
]

data["nodes"].extend(pony_nodes)
data["nodes"].extend(v16_nodes)

max_link_id = max([l[0] for l in data["links"]])
def next_link():
    global max_link_id
    max_link_id += 1
    return max_link_id

# Link definitions
def add_link(src_node, src_slot, dest_node, dest_slot, slot_type):
    lid = next_link()
    # Update src node outputs array
    for gn in data["nodes"]:
        if gn["id"] == src_node:
            if "outputs" in gn and len(gn["outputs"]) > src_slot:
                if "links" not in gn["outputs"][src_slot]:
                    gn["outputs"][src_slot]["links"] = []
                if gn["outputs"][src_slot]["links"] is None:
                    gn["outputs"][src_slot]["links"] = []
                gn["outputs"][src_slot]["links"].append(lid)
    # Update dest node inputs array
    for gn in data["nodes"]:
        if gn["id"] == dest_node:
            if "inputs" in gn and len(gn["inputs"]) > dest_slot:
                gn["inputs"][dest_slot]["link"] = lid
    data["links"].append([lid, src_node, src_slot, dest_node, dest_slot, slot_type])

# Connect Pony
add_link(P_CKPT, 0, P_KSAMPLER, 0, "MODEL")
add_link(P_CKPT, 1, P_CLIP_POS, 0, "CLIP")
add_link(P_CKPT, 1, P_CLIP_NEG, 0, "CLIP")
add_link(P_CKPT, 2, P_VAE_DEC, 1, "VAE")
add_link(P_LATENT, 0, P_KSAMPLER, 3, "LATENT")
add_link(P_CLIP_POS, 0, P_KSAMPLER, 1, "CONDITIONING")
add_link(P_CLIP_NEG, 0, P_KSAMPLER, 2, "CONDITIONING")
add_link(P_KSAMPLER, 0, P_VAE_DEC, 0, "LATENT")

# Connect Qwen Swap
add_link(P_VAE_DEC, 0, P_QWEN, 0, "IMAGE")
add_link(P_SELFIE, 0, P_QWEN, 1, "IMAGE")

# Connect Qwen Output -> ImageScale
add_link(P_QWEN, 0, IMG_SCALE, 0, "IMAGE")

# Connect ImageScale -> ApplyFaceProcessor and WanVaceToVideo
add_link(FACE_LOAD, 0, FACE_APPLY, 0, "FACE_PROCESSOR")
add_link(IMG_SCALE, 0, FACE_APPLY, 1, "IMAGE")

# WanVaceToVideo (Node 34 in Rapid-AIO) input `start_image` is slot 0, but sometimes it depends on rapid array order
for node in data["nodes"]:
    if node["id"] == 34:
        for idx, inp in enumerate(node.get("inputs", [])):
            if inp.get("name") in ["image", "start_image"]:
                add_link(IMG_SCALE, 0, 34, idx, "IMAGE")
                break
    elif node["id"] == 28:
        for idx, inp in enumerate(node.get("inputs", [])):
            if inp.get("name") == "reference_image":
                add_link(FACE_APPLY, 0, 28, idx, "IMAGE")
                break
    elif node["id"] == 26:  # CheckpointLoaderSimple (Wan 2.1)
        pass # Will route link to Lora manually
    elif node["id"] == 32:  # ModelSamplingSD3
        pass # Will route from lora

# LoRA Routing
# CheckpointLoaderSimple (Node 26) output 0 to LoRALoader (LORA_LOAD)
# LORA_LOAD output 0 to ModelSamplingSD3 (Node 32) input 0
# We must first remove the old link between 26 and 32 if it exists, wait we already did (Link 150)
add_link(26, 0, LORA_LOAD, 0, "MODEL")
add_link(LORA_LOAD, 0, 32, 0, "MODEL")

# Overwrite unused LoadImage Node 16 logic (it was removed from links, we do not need it anymore)
for node in data["nodes"]:
    if node["id"] == 16:
        # Orphan it entirely
        if "outputs" in node and len(node["outputs"]) > 0:
            node["outputs"][0]["links"] = []

data["last_node_id"] = max([n["id"] for n in data["nodes"]]) + 10
data["last_link_id"] = max([l[0] for l in data["links"]]) + 10

# Output writing
with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Ultimate MEGA V17 Pipeline Generated: {dest_path}")
