import os
import json
from pathlib import Path

CONFIG_FILE = "qrng_config.json"
DEFAULTS = {
    "sequence_counter": 1,
    "raw_path": str(Path.home() / "Documents" / "qrng_raw"),
    "extracted_path": str(Path.home() / "Documents" / "qrng_extracted"),
    "report_path": str(Path.home() / "Documents" / "qrng_report"),
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULTS.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def increment_counter(config):
    if "sequence_counter" not in config:
        config["sequence_counter"] = 1
    else:
        config["sequence_counter"] += 1
        
    save_config(config)
    return config 

def get_next_filenames(config, method_name):
    idx = config["sequence_counter"]
    prefix = f"{idx:04d}"
    
    raw_file = os.path.join(config["raw_path"], f"raw{prefix}.bin")
    ext_file = os.path.join(config["extracted_path"], f"extracted{prefix}_{method_name}.bin")
    rep_file = os.path.join(config["report_path"], f"report{prefix}_{method_name}.txt")
    
    return raw_file, ext_file, rep_file