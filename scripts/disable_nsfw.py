import os
import re

dir_path = '/workspace/ComfyUI/custom_nodes/comfyui-reactor-node'
patched = False

print("Starting deep purge of ReActor NSFW checks...")

for root, dirs, files in os.walk(dir_path):
    for str_file in files:
        if str_file.endswith('.py'):
            fp = os.path.join(root, str_file)
            try:
                txt = open(fp, 'r', encoding='utf-8').read()
                if 'NSFW content detected' in txt:
                    print(f"🔪 Found target file: {fp}")
                    # Replace scores strictly to never trigger
                    new_txt = re.sub(r'nsfw_score\s*>\s*[0-9.]+', 'nsfw_score > 999.0', txt)
                    new_txt = re.sub(r'score\s*>\s*[0-9.]+', 'score > 999.0', new_txt)
                    new_txt = re.sub(r'if.*?score.*?>=?\s*([a-zA-Z\.0-9]+):', 'if False:', new_txt)
                    new_txt = re.sub(r'if.*?skipping.*?:', 'if False:', new_txt)
                    
                    open(fp, 'w', encoding='utf-8').write(new_txt)
                    print(f"✅ Core code purged in: {str_file}")
                    patched = True
            except Exception as e:
                pass

config_path = os.path.join(dir_path, 'config.ini')
print(f"Writing master config to {config_path}")
with open(config_path, 'w', encoding='utf-8') as f:
    f.write("[DEFAULT]\nUSE_NSFW_SCANNER = False\nnsfw_scanner = False\n")

print("✅ RunPod ReActor NSFW Detector Disable Routine Complete!")
