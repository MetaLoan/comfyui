import json
import os

source_path = "/tmp/Rapid-AIO-Mega.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_mega_aio_workflow.json')

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

    elif node["type"] == "KSampler":
        node["widgets_values"][2] = 15 # steps
        node["widgets_values"][4] = "euler" # sampler
        node["widgets_values"][5] = "beta" # beta scheduler

    elif node["type"] == "WanVaceToVideo":
        # Drop structural control further to prioritize positive prompt identity tags
        for i, v in enumerate(node["widgets_values"]):
            if isinstance(v, float) and (v == 1.0 or v == 0.7):
                node["widgets_values"][i] = 0.6
                
    elif node["type"] == "PrimitiveInt" and node["id"] == 48:
        # Lower frame count from 81 to 49 for faster testing and less drift potential in early tests
        node["widgets_values"][0] = 49

    elif node["type"] == "CLIPTextEncode":
        # Node 9 = Positive Prompt
        if node["id"] == 9:
            original_prompt = node["widgets_values"][0]
            new_prompt = "(exact same ethnicity as reference:1.6), (Asian woman, East Asian features:1.5), (preserve original ethnicity:1.5), identical face identity, consistent racial characteristics, almond-shaped eyes, natural skin tone, no caucasian features, no european facial structure, (photorealistic portrait of the same person:1.4), face remains exactly the same throughout all frames, no face reconstruction, no beautification drift, detailed original facial structure, " + str(original_prompt)
            node["widgets_values"][0] = new_prompt
            
        # Node 10 = Negative Prompt
        if node["id"] == 10:
            # We must clear the accidental positive tags we appended before!
            node["widgets_values"][0] = "caucasian, white woman, european face, big blue eyes, high nose bridge, different ethnicity, race changed, mixed race, generic beautified face, blurry, deformed, ugly, extra limbs, bad anatomy, watermelon"

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ MEGA AIO Native Workflow Generated with Anti-Race-Drift Constraints: {dest_path}")
