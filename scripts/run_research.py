"""Run a documented experiment from a JSON configuration.

Example: python -m scripts.run_research --config configs/pilot.json
"""
import argparse
import json
from pathlib import Path
from src.wavelet_bc7.research import Configuration, Method, run
from src.wavelet_bc7.analysis import analyze

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to JSON experiment configuration")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not Path(data["dataset_manifest"]).is_absolute():
        data["dataset_manifest"] = str((config_path.parent.parent / data["dataset_manifest"]).resolve())
    if not Path(data["output_directory"]).is_absolute():
        data["output_directory"] = str((config_path.parent.parent / data["output_directory"]).resolve())
    if not Path(data.get("texconv_executable", "tools/texconv.exe")).is_absolute():
        data["texconv_executable"] = str((config_path.parent.parent / data.get("texconv_executable", "tools/texconv.exe")).resolve())
    data["methods"] = tuple(Method(**item) for item in data.get("methods", []))
    results = run(Configuration(**data))
    print("Raw:", results)
    print("Paired:", analyze(results))

if __name__ == "__main__":
    main()
