import json
import os

source_path = "/tmp/Rapid-AIO-Mega.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_mega_aio_workflow.json')

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for node in data["nodes"]:
    if node["type"] == "CheckpointLoaderSimple":
        # Put the user's safely renamed model in the native checkpoints folder!
        node["widgets_values"][0] = "wan/Wan2_1-I2V-14B-nsfw.safetensors"
    
    elif node["type"] == "WanVideoVACEStartToEndFrame":
        # Disconnect end_image for standard I2V (forward only)
        for inp in node.get("inputs", []):
            if inp.get("name") == "end_image":
                link_id_to_remove = inp.get("link")
                if link_id_to_remove is not None:
                    data["links"] = [l for l in data["links"] if l[0] != link_id_to_remove]
                inp["link"] = None

    elif node["type"] == "KSampler":
        # Index layout for KSampler widgets natively is usually:
        # 0: seed, 1: control_after_generate, 2: steps, 3: cfg, 4: sampler_name, 5: scheduler
        node["widgets_values"][2] = 12 # bump steps to 12
        node["widgets_values"][4] = "euler" # sampler
        node["widgets_values"][5] = "beta" # beta scheduler is ideal here

    elif node["type"] == "WanVaceToVideo":
        # Drop strength from 1.0 down to 0.7 to avoid structure overriding identity
        for i, v in enumerate(node["widgets_values"]):
            if isinstance(v, float) and v == 1.0:
                node["widgets_values"][i] = 0.7
                
    elif node["type"] == "CLIPTextEncode" and node["id"] == 10:
        original_prompt = node["widgets_values"][0]
        # Reinforce facial identity per the web search suggestions
        new_prompt = "(same woman as the reference image:1.4), (identical face:1.5), (preserve facial identity:1.4), (consistent face throughout:1.3), detailed face, same person, no face change, " + str(original_prompt)
        node["widgets_values"][0] = new_prompt

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ MEGA AIO Native Workflow Generated: {dest_path}")
