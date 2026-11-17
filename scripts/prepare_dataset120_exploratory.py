"""Prepare a clearly labeled, non-inferential 120-image exploratory experiment.

No train/validation/test split is invented. For thesis-grade independent evaluation,
first supply verified provenance and generate manifest_v2.csv with validate_dataset.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

CATEGORIES = ("brick", "fabric", "metal", "organic", "stone", "wood")
STRENGTHS = (0.5, 1.0, 2.0, 4.0)

def prepare(root: Path, output: Path, *, sweep: bool = False) -> tuple[Path, Path]:
    root = root.resolve()
    output = output.resolve()
    files = sorted(root.glob("*.png"))
    expected = {f"{category}_{i:02d}" for category in CATEGORIES for i in range(1, 21)}
    actual = {p.stem.lower() for p in files}
    if len(files) != 120 or actual != expected:
        raise ValueError(f"Expected exactly 120 images (6x20); missing={sorted(expected-actual)}; extra={sorted(actual-expected)}")
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "exploratory_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=("image_id", "path", "split", "material_group"))
        writer.writeheader()
        for p in files:
            writer.writerow({"image_id": p.stem.lower(), "path": __import__("os").path.relpath(p, manifest.parent).replace("\\", "/"),
                             "split": "exploratory", "material_group": p.stem.split("_")[0].lower()})
    methods = [{"name":"baseline","mode":"identity","strength":0}]
    for mode in ("fixed", "adaptive"):
        for strength in (STRENGTHS if sweep else (4.0,)):
            methods.append({"name":f"{mode}_{str(strength).replace('.', 'p')}",
                            "mode":mode, "strength":strength})
    config = output / ("exploratory_sweep.json" if sweep else "exploratory_3methods.json")
    config.write_text(json.dumps({
        "dataset_manifest": str(manifest), "output_directory": str(output / ("sweep_results" if sweep else "comparison_results")),
        "texconv_executable": str((Path.cwd() / "tools" / "texconv.exe").resolve()),
        "backend": "cpu", "split": "exploratory", "methods": methods
    }, indent=2), encoding="utf-8")
    (output / "READ_ME_FIRST.txt").write_text(
        "EXPLORATORY ONLY: 120 files, no verified source groups or independent train/validation/test. "
        "Do not report significance or generalization; select parameters on validation only after provenance review.\n",
        encoding="utf-8")
    return manifest, config

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("resources/textures/train/albedo"))
    p.add_argument("--output", type=Path, default=Path("results/experiments/dataset120_exploratory"))
    p.add_argument("--sweep", action="store_true")
    args = p.parse_args()
    manifest, config = prepare(args.root, args.output, sweep=args.sweep)
    print("Manifest:", manifest)
    print("Config:", config)

if __name__ == "__main__":
    main()
