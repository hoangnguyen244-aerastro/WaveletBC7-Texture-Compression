"""Prepare the locked 24-image held-out test from validation-only selection."""
import argparse
import csv
import json
from pathlib import Path

MATERIALS=("brick","fabric","metal","organic","stone","wood")

def prepare(selection:Path,manifest:Path,output:Path,material:str):
    if material not in MATERIALS: raise ValueError(material)
    decision=json.loads(selection.read_text(encoding="utf-8"))
    if decision["n_validation_images"]!=24: raise ValueError("Selection not based on complete validation")
    with manifest.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if len(rows)!=120: raise ValueError("Expected frozen 120-image manifest")
    selected=[r for r in rows if r["material_group"]==material and r["split"]=="test"]
    if len(selected)!=4: raise ValueError("Expected exactly 4 held-out test images per material")
    output.mkdir(parents=True,exist_ok=True)
    local_manifest=output/f"test_{material}.csv"
    with local_manifest.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=("image_id","path","split","material_group"))
        writer.writeheader()
        # Paths in original manifest are relative to manifest parent, not this new output directory.
        for r in selected:
            from os.path import relpath
            src=(manifest.parent/r["path"]).resolve()
            writer.writerow({**r,"path":relpath(src,output).replace("\\","/")})
    methods=[{"name":"baseline","mode":"identity","strength":0.0}]
    for mode in ("fixed","adaptive"):
        chosen=decision["selected"][mode]
        methods.append({"name":chosen["name"],"mode":mode,"strength":chosen["strength"]})
    config={"dataset_manifest":str(local_manifest.resolve()),"output_directory":str((output/f"test_results_{material}").resolve()),
            "texconv_executable":str((Path.cwd()/"tools"/"texconv.exe").resolve()),
            "backend":"cpu","split":"test","methods":methods}
    (output/f"test_{material}.json").write_text(json.dumps(config,indent=2),encoding="utf-8")
    print(json.dumps(config,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--selection",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("results/experiments/v3_test"))
    p.add_argument("--material",required=True,choices=MATERIALS)
    a=p.parse_args()
    prepare(a.selection,a.manifest,a.output,a.material)
