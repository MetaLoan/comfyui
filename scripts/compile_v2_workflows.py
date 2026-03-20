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

new_nodes = []
for node in data["nodes"]:
    if node["id"] == 22: # WanVideoModelLoader
        # ["WanVideo\\Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors", "fp16", "fp8_e4m3fn", "offload_device", "sdpa"]
        node["widgets_values"][0] = "wan/wan2.2-rapid-mega-aio-nsfw-v10.safetensors"
        node["widgets_values"][1] = "bf16" # Model is safetensors, load as bf16
        node["widgets_values"][2] = "bf16"
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
        # We repurpose this to load the NSFW LoRA
        node["widgets_values"][0] = "nsfw_motion/wan_nsfw_e14.safetensors"
        node["widgets_values"][1] = 1.0 # strength
        
# ------------------------------------------------------------------------------------------
# --- 1. First, save the NON-LIGHTNING (high quality) V2 workflow ---
# ------------------------------------------------------------------------------------------
# Find sampler to set high quality steps
for node in data["nodes"]:
    if node["id"] == 27:
        node["widgets_values"][0] = 30 # 30 steps for standard quality

lora_dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_i2v_nsfw_lora.json')
with open(lora_dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------------------------------
# --- 2. Second, mutate data to add Lightning LoRA and save LIGHTNING V2 workflow ---
# ------------------------------------------------------------------------------------------
for node in data["nodes"]:
    if node["id"] == 27:
        node["widgets_values"][0] = 4 # 4 steps for lightning
    
    if node["id"] == 69:
        # Now we insert a SECOND LoRA node for Lightning
        new_lora = {
            "id": 169,
            "type": "WanVideoLoraSelect",
            "pos": [node["pos"][0], node["pos"][1] - 200],
            "size": [583, 176],
            "flags": {},
            "order": node["order"] + 1,
            "mode": 0,
            "inputs": [{"name": "prev_lora", "type": "WANVIDLORA", "link": 189}],
            "outputs": [{"name": "lora", "type": "WANVIDLORA", "links": [190]}],
            "properties": {"Node name for S&R": "WanVideoLoraSelect"},
            "widgets_values": ["lightning/lightx2v_I2V_14B_480p.safetensors", 1.0, False, ""]
        }
        new_nodes.append(new_lora)
        
        # Original node 69 outputting to 22 via link [89, 69, 0, 22, 2, "WANVIDLORA"]
        # We will change it so 69 -> 169 -> 22
        # First remove link 89
        data["links"] = [l for l in data["links"] if l[0] != 89]
        # Add links
        data["links"].append([189, 69, 0, 169, 0, "WANVIDLORA"])  # 69 -> 169
        data["links"].append([190, 169, 0, 22, 2, "WANVIDLORA"]) # 169 -> 22

data["nodes"].extend(new_nodes)

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ V2 Lightning & Lora Jsons Generated: {dest_path}")
