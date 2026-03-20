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
            # We must use a completely universal race-agnostic locking prompt so the user can use any image safely
            base_prompt = "(exact same person as the reference image:1.6), (identical facial identity:1.6), (preserve original face exactly:1.5), (consistent character identity throughout all frames:1.5), (same face, no face change, no identity drift, no reconstruction, no beautification, no morphing:1.4), face remains exactly the same person from start to end, photorealistic portrait fidelity, detailed original facial features and structure, natural skin texture and pores as in input image, no alterations to facial appearance, "
            action_prompt = "woman performing blowjob, close-up on face only, POV angle from above, erect penis entering and sliding in and out of her mouth, lips tightly wrapped around shaft, tongue visibly licking underside, saliva dripping from mouth corners and chin with glossy strands, eyes looking up seductively at viewer, slight gag reflex on deep thrusts, cheeks hollowing intensely while sucking, wet glistening lips and lower face, head moving forward and backward rhythmically, slow deep throating first 2 seconds then faster bobbing for remaining time, smooth fluid head motion and oral action, erotic focused pleasure expression, high detail realistic skin and saliva, smooth and fluid motion, static camera, high quality, detailed realistic lighting, consistent identity, stable facial features, clean minimal background"
            node["widgets_values"][0] = base_prompt + action_prompt
            
        # Node 10 = Negative Prompt
        if node["id"] == 10:
            node["widgets_values"][0] = "different person, identity change, identity drift, face reconstruction, face morphing, beautified face, generic face, altered facial features, race change, ethnicity change, different ethnicity, caucasian features, european face, asian features if not original, any skin tone change, eye shape change, nose change, lip change, asymmetrical face, distorted face, deformed eyes, deformed mouth, extra teeth, bad anatomy, mutated face, off-model face, wrong facial structure, blurry face, low detail face, overexposed skin, unnatural skin, artifacts on face, motion blur on face, closed mouth the whole time, no saliva, no penis, censored, mosaic, text, watermark, ugly, poorly drawn face, extra limbs, bad proportions, grainy, flickering face, reward hacking stiffness, frozen expression"

# --- Inject Image Resizer to prevent OOM ---
data["nodes"].append({
  "id": 100,
  "type": "ImageResizeKJv2",
  "pos": [100, 100],
  "size": [270, 336],
  "flags": {},
  "order": 1,
  "mode": 0,
  "inputs": [
    {"name": "image", "type": "IMAGE", "link": 156} # Hijack link 156 from Node 37
  ],
  "outputs": [
    {"name": "IMAGE", "type": "IMAGE", "links": [1001]}
  ],
  "properties": {"Node name for S&R": "ImageResizeKJv2"},
  "widgets_values": [832, 480, "nearest-exact", "stretch", "0, 0, 0", "center", 2, "cpu"]
})

# Update Link 156 destination: It originally went to Node 34 slot 1.
# Now Link 156 goes to Node 100 (ImageResize) slot 0
for link in data["links"]:
    if link[0] == 156:
        # [id, from_node, from_slot, to_node, to_slot, type]
        link[3] = 100 # to_node
        link[4] = 0   # to_slot

# Add Link 1001 from Node 100 to Node 34 (StartToEndFrame image)
data["links"].append([1001, 100, 0, 34, 1, "IMAGE"])

# Add Link 1002 from Node 100 to Node 28 (WanVaceToVideo reference_image)
data["links"].append([1002, 100, 0, 28, 5, "IMAGE"])

# Update Node 34 to receive Link 1001 instead of 156
for node in data["nodes"]:
    if node["id"] == 34:
        for inp in node.get("inputs", []):
            if inp.get("name") == "image":
                inp["link"] = 1001
    
    # Update Node 28 to receive Link 1002 for reference_image
    elif node["id"] == 28:
        for inp in node.get("inputs", []):
            if inp.get("name") == "reference_image":
                inp["link"] = 1002

with open(dest_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ MEGA AIO Native Workflow Generated with Anti-Race-Drift Constraints: {dest_path}")
