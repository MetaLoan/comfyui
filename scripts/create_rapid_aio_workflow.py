import json
import os

source_path = "/tmp/Rapid-AIO-Mega.json"
dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows', 'wan2.2_mega_aio_v10.json')

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Process all nodes - modify in-place only, no new node injection
for node in data["nodes"]:

    if node["type"] == "CheckpointLoaderSimple":
        node["widgets_values"][0] = "wan/Wan2_1-I2V-14B-nsfw.safetensors"

    elif node["type"] == "WanVideoVACEStartToEndFrame":
        # Disconnect end_image to allow pure I2V (start frame only)
        for inp in node.get("inputs", []):
            if inp.get("name") == "end_image":
                link_id_to_remove = inp.get("link")
                if link_id_to_remove is not None:
                    data["links"] = [l for l in data["links"] if l[0] != link_id_to_remove]
                inp["link"] = None

    elif node["type"] == "WanVaceToVideo":
        # widgets_values = [width, height, frames, something, something]
        # Cap resolution to 832x480 to prevent GPU OOM.
        # DO NOT modify the last two 1.0 values! They are integer mode triggers (1=I2V, 0=T2V).
        node["widgets_values"][0] = 832   # width
        node["widgets_values"][1] = 480   # height

    elif node["type"] == "KSampler":
        node["widgets_values"][2] = 15  # steps
        node["widgets_values"][4] = "euler"  # sampler
        node["widgets_values"][5] = "beta"  # scheduler

    elif node["type"] == "PrimitiveInt" and node["id"] == 48:
        node["widgets_values"][0] = 49  # 49 frames for test

    elif node["type"] == "CLIPTextEncode":
        if node["id"] == 9:  # Positive prompt
            base = "(exact same person as the reference image:1.6), (identical facial identity:1.6), (preserve original face exactly:1.5), (consistent character identity throughout all frames:1.5), (same face, no face change, no identity drift, no reconstruction, no beautification, no morphing:1.4), face remains exactly the same person from start to end, photorealistic portrait fidelity, detailed original facial features and structure, natural skin texture and pores as in input image, no alterations to facial appearance, "
            action = "woman performing blowjob, close-up on face only, POV angle from above, erect penis entering and sliding in and out of her mouth, lips tightly wrapped around shaft, tongue visibly licking underside, saliva dripping from mouth corners and chin with glossy strands, eyes looking up seductively at viewer, slight gag reflex on deep thrusts, cheeks hollowing intensely while sucking, wet glistening lips and lower face, head moving forward and backward rhythmically, slow deep throating first 2 seconds then faster bobbing for remaining time, smooth fluid head motion and oral action, erotic focused pleasure expression, high detail realistic skin and saliva, smooth and fluid motion, static camera, high quality, detailed realistic lighting, consistent identity, stable facial features, clean minimal background"
            node["widgets_values"][0] = base + action

        elif node["id"] == 10:  # Negative prompt
            node["widgets_values"][0] = "different person, identity change, identity drift, face reconstruction, face morphing, beautified face, generic face, altered facial features, race change, ethnicity change, different ethnicity, any skin tone change, eye shape change, nose change, lip change, asymmetrical face, distorted face, deformed eyes, deformed mouth, extra teeth, bad anatomy, mutated face, off-model face, wrong facial structure, blurry face, low detail face, overexposed skin, unnatural skin, artifacts on face, motion blur on face, closed mouth the whole time, no saliva, no penis, censored, mosaic, text, watermark, ugly, poorly drawn face, extra limbs, bad proportions, grainy, flickering face, frozen expression"

# Also wire reference_image on WanVaceToVideo to receive the start image (link 161)
# The start image is sent from Node 16 (LoadImage) via link 161 to Node 34.
# We add a SECOND copy of these link slots: link 161 can only have 1 destination,
# so instead we clone the image by updating Node 16 to output 2 links and add a new link 2001.
# Find node 16 and add 2001 to its output[0].links
for node in data["nodes"]:
    if node["id"] == 16:  # LoadImage (start image)
        if node["outputs"]:
            if isinstance(node["outputs"][0].get("links"), list):
                node["outputs"][0]["links"].append(2001)
    elif node["id"] == 28:  # WanVaceToVideo
        for inp in node.get("inputs", []):
            if inp.get("name") == "reference_image":
                inp["link"] = 2001

# Add link 2001: Node 16 → Node 28 reference_image (slot 5)
data["links"].append([2001, 16, 0, 28, 5, "IMAGE"])

data["last_node_id"] = max([n["id"] for n in data["nodes"]]) + 10
data["last_link_id"] = max([l[0] for l in data["links"]]) + 10

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ v9 workflow (no injected nodes, resolution capped via WanVaceToVideo): {dest_path}")
