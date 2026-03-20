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
                # Find the link id
                link_id_to_remove = inp.get("link")
                if link_id_to_remove is not None:
                    # Remove it from global links
                    data["links"] = [l for l in data["links"] if l[0] != link_id_to_remove]
                inp["link"] = None

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ MEGA AIO Native Workflow Generated: {dest_path}")
