import json
import os

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base_workflow = os.path.join(repo_dir, 'workflows', 'wan2.2_i2v_nsfw_lora.json')
lightning_workflow = os.path.join(repo_dir, 'workflows', 'wan2.2_i2v_nsfw_lightning.json')

with open(base_workflow, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update info
data['_info'] = "Wan 2.2 I2V NSFW + Lightning极速版工作流 — 只要4步，2分钟出图"

# Append a new LoraLoaderModelOnly node for Lightning
new_node_id = 12
lightning_node = {
    "id": new_node_id,
    "type": "LoraLoaderModelOnly",
    "pos": [450, -60],
    "size": [380, 120],
    "flags": {},
    "order": 10,
    "mode": 0,
    "inputs": [
    {"name": "model", "type": "WANVIDEOMODEL", "link": 14} # Will take input from Node 4 (NSFW LoRA)
    ],
    "outputs": [{"name": "MODEL", "type": "WANVIDEOMODEL", "links": [15]}],
    "properties": {"Node name for S&R": "LoraLoaderModelOnly"},
    "widgets_values": ["lightning/lightx2v_I2V_14B_480p.safetensors", 1.0]
}
data["nodes"].append(lightning_node)

# We need to change the flow: 
# Original: Node 4 (NSFW Lora) -> Node 9 (Sampler) [Link ID 5]
# New flow: Node 4 (NSFW Lora) -> Node 12 (Lightning Lora) -> Node 9 (Sampler)

# 1. First remove the old link [5, 4, 0, 9, 0, "WANVIDEOMODEL"]
data["links"] = [link for link in data["links"] if link[0] != 5]

# 2. Add the two new links
# link [14, 4, 0, 12, 0, "WANVIDEOMODEL"] (Node 4 -> Node 12)
# link [15, 12, 0, 9, 0, "WANVIDEOMODEL"] (Node 12 -> Node 9)
data["links"].append([14, 4, 0, 12, 0, "WANVIDEOMODEL"])
data["links"].append([15, 12, 0, 9, 0, "WANVIDEOMODEL"])

# 3. Update the inputs on Node 9 and Node 12
for node in data["nodes"]:
    if node["id"] == 9: # Sampler
        for inp in node["inputs"]:
            if inp["name"] == "model":
                inp["link"] = 15 # Now comes from Lightning LoRA
        # Also change Sampler steps to 4 and CFG to 1.0 for Lightning!
        # [42, "euler", "sgm_uniform", 30, 6.0, 1, true] -> [42, "euler", "sgm_uniform", 4, 1.0, 1, true]
        node["widgets_values"][3] = 4
        node["widgets_values"][4] = 1.0
        
data["last_node_id"] = 12
data["last_link_id"] = 15

with open(lightning_workflow, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Lightning 工作流已创建: wan2.2_i2v_nsfw_lightning.json")
