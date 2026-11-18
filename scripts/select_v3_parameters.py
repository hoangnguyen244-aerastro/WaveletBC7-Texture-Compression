"""Select strengths from six validation CSVs, never from held-out test images."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

MATERIALS=("brick","fabric","metal","organic","stone","wood")
STRENGTHS=("0p5","1p0","2p0","4p0")

def select(artifacts: Path, output: Path):
    rows=[]
    for material in MATERIALS:
        candidates=list(artifacts.rglob(f"v3-validation-{material}/raw_results.csv"))
        if len(candidates)!=1:
            raise ValueError(f"Expected exactly one validation CSV for {material}; got {candidates}")
        with candidates[0].open(newline="",encoding="utf-8") as f:
            material_rows=list(csv.DictReader(f))
        if len(material_rows)!=36:
            raise ValueError(f"Expected 36 validation rows for {material}; got {len(material_rows)}")
        images={r["image_id"] for r in material_rows}
        if len(images)!=4 or any(r["material_group"]!=material or r["split"]!="validation" for r in material_rows):
            raise ValueError(f"Invalid validation manifest for {material}")
        expected={"baseline"}|{f"{mode}_{strength}" for mode in ("fixed","adaptive") for strength in STRENGTHS}
        for image in images:
            methods=[r["method"] for r in material_rows if r["image_id"]==image]
            if len(methods)!=9 or set(methods)!=expected:
                raise ValueError(f"Missing or duplicate validation method for {image}")
        rows.extend(material_rows)
    baselines={r["image_id"]:float(r["psnr_db"]) for r in rows if r["method"]=="baseline"}
    if len(baselines)!=24:
        raise ValueError("Expected 24 independent baseline images")
    diffs=defaultdict(list)
    for r in rows:
        if r["method"]!="baseline":
            diffs[r["method"]].append(float(r["psnr_db"])-baselines[r["image_id"]])
    scores={method:sum(values)/len(values) for method,values in diffs.items() if len(values)==24}
    if len(scores)!=8:
        raise ValueError("Incomplete validation scores")
    winners={}
    for mode in ("fixed","adaptive"):
        winner=max((m for m in scores if m.startswith(mode+"_")),key=lambda m:(scores[m],m))
        winners[mode]={"name":winner,"mode":mode,"strength":float(winner.split("_")[1].replace("p",".")),
                       "validation_mean_delta_psnr_db":scores[winner]}
    result={"selection_metric":"mean paired PSNR difference (dB) on 24 validation images",
            "n_validation_images":24,"validation_scores":scores,"selected":winners,
            "rule":"No held-out test result used for selection."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("results/experiments/v3/selection.json"))
    a=p.parse_args()
    select(a.artifacts,a.output)
