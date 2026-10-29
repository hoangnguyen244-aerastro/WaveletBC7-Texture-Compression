"""Generate PSNR–strength curves from real raw_results.csv."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot(raw):
    raw=Path(raw)
    with raw.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    baseline={r["image_id"]:float(r["psnr_db"]) for r in rows if r["mode"]=="identity"}
    if not baseline: raise ValueError("Missing baseline rows")
    data={}
    for r in rows:
        if r["mode"]=="identity": continue
        if r["image_id"] not in baseline: raise ValueError("Unpaired image")
        key=(r["mode"],float(r["strength"]))
        data.setdefault(key,[]).append(float(r["psnr_db"])-baseline[r["image_id"]])
    fig,ax=plt.subplots(figsize=(8,5))
    for mode in ("fixed","adaptive"):
        pairs=sorted((strength,np.mean(v)) for (m,strength),v in data.items() if m==mode)
        if pairs:
            ax.plot([x for x,y in pairs],[y for x,y in pairs],marker="o",label=mode)
    ax.axhline(0,color="gray",linestyle="--")
    ax.set(xlabel="Wavelet strength",ylabel="Mean ΔPSNR vs BC7 (dB)",title="Wavelet strength sweep")
    ax.legend()
    fig.tight_layout()
    out=raw.parent/"figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out/"psnr_strength.png",dpi=300)
    fig.savefig(out/"psnr_strength.svg")
    plt.close(fig)
    return out/"psnr_strength.png"

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("raw_csv")
    print(plot(p.parse_args().raw_csv))
