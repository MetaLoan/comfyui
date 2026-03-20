import json
import os

source_path = "/tmp/wan_v2_example.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_i2v_nsfw_lightning.json')

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Delete nodes 59 (CLIPVisionLoader) and 65 (WanVideoClipVisionEncode)
# And delete Native ComfyUI Text Encoders: 46 (WanVideoTextEmbedBridge), 48 (CLIPLoader), 49 (CLIPTextEncode), 50 (CLIPTextEncode)
# (In V2 example, it has both native and kijai text encodes, we will use the Kijai one which is Node 16)
nodes_to_delete = {46, 48, 49, 50, 59, 65}
data["nodes"] = [n for n in data["nodes"] if n["id"] not in nodes_to_delete]

# Clean links
links_to_keep = []
for link in data["links"]:
    # link = [link_id, from_node, from_slot, to_node, to_slot, type]
    if (link[1] not in nodes_to_delete) and (link[3] not in nodes_to_delete):
        links_to_keep.append(link)

# Reset links that go into Node 27 (Sampler) slot 1 (image_embeds) because we deleted WanVideoClipVisionEncode
# Node 63 (WanVideoImageToVideoEncode) outputs image_embeds?
# Looking closely at Kijai's V2, WanVideoImageToVideoEncode (id 63) takes clip_embeds from 65. If we don't have 65, we must remove link 82 going into 63 slot 1.
links_to_keep = [l for l in links_to_keep if l[0] != 82] # remove link to clip_embeds
# WanVideoImageToVideoEncode (id 63) STILL outputs image_embeds? Yes.
# And WanVideoTextEncode (id 16) outputs text_embeds? Yes.
data["links"] = links_to_keep

# Clean up dangling links in node inputs
for node in data["nodes"]:
    if "inputs" in node:
        for inp in node["inputs"]:
            if "link" in inp and inp["link"] is not None:
                if not any(l[0] == inp["link"] for l in links_to_keep):
                    inp["link"] = None

new_nodes = []
for node in data["nodes"]:
    if node["id"] == 22: # WanVideoModelLoader
        # Kijai's node looks in models/diffusion_models 
        # MUST rename to include "14B" to satisfy Kijai's hardcoded parameter size logic!
        node["widgets_values"][0] = "Wan2_1-I2V-14B-nsfw.safetensors"
        node["widgets_values"][1] = "bf16" # base_precision
        node["widgets_values"][2] = "disabled" # quantization MUST be 'disabled', not 'bf16'
    elif node["id"] == 11: # LoadWanVideoT5TextEncoder
        node["widgets_values"][0] = "umt5_xxl.pth" # From models/text_encoders
        node["widgets_values"][1] = "bf16"
    elif node["id"] == 38: # WanVideoVAELoader
        node["widgets_values"][0] = "Wan2.1_VAE.pth"
        node["widgets_values"][1] = "bf16"
    elif node["id"] == 16: # WanVideoTextEncode
        node["widgets_values"][0] = "woman from behind, doggy style position, realistic thrusting motion, hips bouncing rhythmically, sweat, cinematic lighting, 8k quality"
        node["widgets_values"][1] = "blurry, deformed, ugly, extra limbs, bad anatomy, watermelon"
    elif node["id"] == 27: # WanVideoSampler
        # Lightning settings!
        # widgets: [steps(4), shift(1), seed, scheduler("fixed"), ...]
        node["widgets_values"][0] = 4
        node["widgets_values"][1] = 1.0 # shift
        # The sampler for lightning usually wants CFG=1.0. In WanVideoSampler V2, where is CFG?
        # Typically CFG is not here, it's shift or something else? We will just keep default feta/sampler args.
    elif node["id"] == 69: # WanVideoLoraSelect (Original)
        # User failed to download nsfw_motion lora due to Civitai restrictions.
        # Use lightning lora here to pass validation. For non-lightning workflow, we set strength to 0.0.
        node["widgets_values"][0] = "lightning/lightx2v_I2V_14B_480p.safetensors"
        node["widgets_values"][1] = 0.0 # Disabled for non-lightning HQ version
        
# ------------------------------------------------------------------------------------------
# --- 1. First, save the NON-LIGHTNING (high quality) V2 workflow ---
# ------------------------------------------------------------------------------------------
for node in data["nodes"]:
    if node["id"] == 27:
        node["widgets_values"][0] = 30 # 30 steps for standard quality

lora_dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_i2v_nsfw_lora.json')
with open(lora_dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------------------------------
# --- 2. Second, mutate data to save LIGHTNING V2 workflow ---
# ------------------------------------------------------------------------------------------
for node in data["nodes"]:
    if node["id"] == 27:
        node["widgets_values"][0] = 4 # 4 steps for lightning
    elif node["id"] == 69:
        node["widgets_values"][1] = 1.0 # Enable lightning strength

data["last_node_id"] = max([n["id"] for n in data["nodes"]]) + 10
data["last_link_id"] = max([l[0] for l in data["links"]]) + 10

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ V2 Lightning & Lora Jsons Generated: {dest_path}")
