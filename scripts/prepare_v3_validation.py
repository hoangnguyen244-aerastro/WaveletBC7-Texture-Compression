"""Freeze an independent-image, material-stratified 72/24/24 split and validation jobs.

Assumption: user confirmed all 120 textures were created independently.
Alpha is ignored by the research runner; source PNGs are never changed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from PIL import Image

GROUPS = ("brick", "fabric", "metal", "organic", "stone", "wood")
STRENGTHS = (0.5, 1.0, 2.0, 4.0)
SEED = "wavelet-bc7-v3-independent-2026-11-18"

def prepare(root: Path, out: Path, material: str) -> None:
    if material not in GROUPS:
        raise ValueError(f"material must be one of {GROUPS}")
    root = root.resolve()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for group in GROUPS:
        paths = sorted(root.glob(f"{group.capitalize()}_*.png"))
        if len(paths) != 20 or {p.stem.lower() for p in paths} != {f"{group}_{i:02d}" for i in range(1,21)}:
            raise ValueError(f"Expected 20 unique {group} images")
        paths.sort(key=lambda p: hashlib.sha256(f"{SEED}:{p.stem.lower()}".encode()).hexdigest())
        for i, path in enumerate(paths):
            with Image.open(path) as im:
                im.load()
                if im.size != (1024,1024) or im.mode not in ("RGB","RGBA"):
                    raise ValueError(f"Invalid texture {path}: {im.mode} {im.size}")
            split = "train" if i < 12 else "validation" if i < 16 else "test"
            all_rows.append({"image_id":path.stem.lower(),"path":os.path.relpath(path,out).replace("\\","/"),
                             "split":split,"material_group":group})
    manifest = out / "manifest_v3.csv"
    with manifest.open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=("image_id","path","split","material_group"))
        writer.writeheader()
        writer.writerows(sorted(all_rows,key=lambda r:r["image_id"]))
    # One category per job, 4 validation images. All methods share the same input.
    selected = [r for r in all_rows if r["material_group"] == material and r["split"] == "validation"]
    local_manifest = out / f"validation_{material}.csv"
    with local_manifest.open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=("image_id","path","split","material_group"))
        writer.writeheader()
        writer.writerows(selected)
    methods = [{"name":"baseline","mode":"identity","strength":0.0}]
    for mode in ("fixed","adaptive"):
        for strength in STRENGTHS:
            methods.append({"name":f"{mode}_{str(strength).replace('.','p')}",
                            "mode":mode,"strength":strength})
    cfg = {"dataset_manifest":str(local_manifest),"output_directory":str(out / f"validation_results_{material}"),
           "texconv_executable":str((Path.cwd()/"tools"/"texconv.exe").resolve()),
           "backend":"cpu","split":"validation","methods":methods}
    (out / f"validation_{material}.json").write_text(json.dumps(cfg,indent=2),encoding="utf-8")
    (out/"split_protocol.json").write_text(json.dumps({"seed":SEED,"independence_assumption":"user-confirmed independently created images",
        "per_material":{"train":12,"validation":4,"test":4},"rgb_only":True,
        "alpha_policy":"ignore alpha without compositing","methods":methods},indent=2),encoding="utf-8")
    print(f"Prepared {material}: 4 validation images x 9 methods; full manifest has {len(all_rows)} images")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--material",required=True,choices=GROUPS)
    p.add_argument("--root",type=Path,default=Path("resources/textures/train/albedo"))
    p.add_argument("--output",type=Path,default=Path("results/experiments/v3"))
    a=p.parse_args()
    prepare(a.root,a.output,a.material)
