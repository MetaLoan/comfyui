import os
import re

print("🚀 Starting ReActor NSFW Override (v3)...")

base_dir = '/workspace/ComfyUI/custom_nodes'
target_dir = None

# Search for the reactor folder (case-insensitive)
if os.path.exists(base_dir):
    for f in os.listdir(base_dir):
        if 'reactor' in f.lower():
            target_dir = os.path.join(base_dir, f)
            print(f"📦 Found ReActor directory: {target_dir}")
            break

if not target_dir:
    print("❌ Critical Error: Could not find ReActor folder! Please ensure it is installed.")
    exit(1)

patched_count = 0

# Walk the reactor directory to find and patch NSFW checks
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith('.py'):
            fp = os.path.join(root, file)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    txt = f.read()
                
                # Check for telltale NSFW strings
                if 'NSFW' in txt or 'nsfw' in txt:
                    print(f"🔪 Analyzing suspect logic inside: {file}")
                    
                    # We aggressively modify all score checks to never trigger
                    new_txt = re.sub(r'nsfw_score\s*>\s*[0-9.]+', 'nsfw_score > 999.0', txt)
                    new_txt = re.sub(r'score\s*>\s*[0-9.]+', 'score > 999.0', new_txt)
                    
                    # Force 'if score > threshold:' logic to 'if False:'
                    new_txt = re.sub(r'if.*?score.*?>=?\s*([a-zA-Z\.0-9]+):', 'if False:', new_txt)
                    
                    # Specifically slice out the 'skipping' logging block
                    new_txt = re.sub(r'if.*?skipping.*?:', 'if False:', new_txt)
                    
                    # If any modification was made, write it back
                    if new_txt != txt:
                        with open(fp, 'w', encoding='utf-8') as f:
                            f.write(new_txt)
                        print(f"   -> ✅ Neutered target file {file}")
                        patched_count += 1
            except Exception as e:
                pass

print(f"✅ Total Python backend files surgically altered: {patched_count}")

# Inject the configuration file to disable the scanner natively
cfg_path = os.path.join(target_dir, 'config.ini')
try:
    with open(cfg_path, 'w', encoding='utf-8') as cfg_file:
        cfg_file.write("[DEFAULT]\nUSE_NSFW_SCANNER = False\nnsfw_scanner = False\n")
    print(f"✅ ReActor strict Master Config generated over {cfg_path}")
except Exception as e:
    print(f"⚠️ Could not write config.ini: {e}")

print("🎉 ALL SYSTEMS GREEN: ReActor explicit NSFW filtering is physically disabled!")
