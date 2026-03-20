import json
import os

source_path = "/tmp/Rapid-AIO-Mega.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_mega_aio_stand_in_lora_v16.json')

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for node in data["nodes"]:
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

for node in data["nodes"]:
    node["mode"] = 0

# ImageScale for memory safety
data["nodes"].append({
  "id": 100, "type": "ImageScale", "pos": [100, 100], "size": [270, 130], "flags": {}, "order": 1, "mode": 0,
  "inputs": [{"name": "image", "type": "IMAGE", "link": 160}],
  "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [1001, 1002]}],
  "properties": {"Node name for S&R": "ImageScale"}, "widgets_values": ["nearest-exact", 832, 480, "disabled"]
})

# StandIn nodes
data["nodes"].append({
  "id": 201, "type": "FaceProcessorLoader", "pos": [100, 400], "size": [315, 60], "flags": {}, "order": 1, "mode": 0,
  "inputs": [],
  "outputs": [{"name": "face_processor", "type": "FACE_PROCESSOR", "links": [2001]}],
  "properties": {"Node name for S&R": "FaceProcessorLoader"}, "widgets_values": ["model.pt"]
})

data["nodes"].append({
  "id": 200, "type": "ApplyFaceProcessor", "pos": [450, 400], "size": [315, 200], "flags": {}, "order": 2, "mode": 0,
  "inputs": [{"name": "face_processor", "type": "FACE_PROCESSOR", "link": 2001}, {"name": "image", "type": "IMAGE", "link": 1002}],
  "outputs": [{"name": "processed_image", "type": "IMAGE", "links": [2003]}, {"name": "face_rgba", "type": "IMAGE", "links": []}],
  "properties": {"Node name for S&R": "ApplyFaceProcessor"}, "widgets_values": [512, 10, 1.35, 0.45, True, False]
})

# Lora Loader Node
data["nodes"].append({
  "id": 300, "type": "LoraLoaderModelOnly", "pos": [950, 600], "size": [315, 120], "flags": {}, "order": 3, "mode": 0,
  "inputs": [{"name": "model", "type": "MODEL", "link": 3001}],
  "outputs": [{"name": "MODEL", "type": "MODEL", "links": [3002]}],
  "properties": {"Node name for S&R": "LoraLoaderModelOnly"}, 
  "widgets_values": ["wan22_i2v_anal_v1_high_noise.safetensors", 0.75] # User can change lora logic here
})


# Filter out old links: Link 161 (LoadImage->VACE) and Link 150 (CheckpointLoader->ModelSamplingSD3)
data["links"] = [l for l in data["links"] if l[0] not in [161, 150]]

# Re-route remaining slot links to match node mappings
for node in data["nodes"]:
    if node["id"] == 16:
        if "outputs" in node and len(node["outputs"]) > 0:
            node["outputs"][0]["links"] = [160]
    elif node["id"] == 34:
        for inp in node.get("inputs", []):
            if inp.get("name") in ["image", "start_image"]:
                inp["link"] = 1001
    elif node["id"] == 28:
        for inp in node.get("inputs", []):
            if inp.get("name") == "reference_image":
                inp["link"] = 2003
    elif node["id"] == 26:  # CheckpointLoaderSimple
        if "outputs" in node and len(node["outputs"]) > 0:
            node["outputs"][0]["links"] = [3001]
    elif node["id"] == 32:  # ModelSamplingSD3
        for inp in node.get("inputs", []):
            if inp.get("name") == "model":
                inp["link"] = 3002

# Standard explicit linking
data["links"].append([160, 16, 0, 100, 0, "IMAGE"]) 
data["links"].append([1001, 100, 0, 34, 0, "IMAGE"])
data["links"].append([1002, 100, 0, 200, 1, "IMAGE"])
data["links"].append([2001, 201, 0, 200, 0, "FACE_PROCESSOR"])
data["links"].append([2003, 200, 0, 28, 5, "IMAGE"]) 

# LoRA Linking
data["links"].append([3001, 26, 0, 300, 0, "MODEL"]) # Checkpoint -> LoraLoaderModelOnly
data["links"].append([3002, 300, 0, 32, 0, "MODEL"]) # LoraLoaderModelOnly -> ModelSamplingSD3

data["last_node_id"] = max([n["id"] for n in data["nodes"]]) + 10
data["last_link_id"] = max([l[0] for l in data["links"]]) + 10

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ LoRA Workflow Generated (v16 Parameter Tuning): {dest_path}")
