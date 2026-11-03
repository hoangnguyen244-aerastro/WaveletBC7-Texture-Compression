"""Paired, per-image analysis; descriptive outputs are not claims of significance."""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np

METRICS = {"psnr_db": 1, "ssim": 1, "mae": -1, "edge_mae": -1}

def bootstrap_ci(values, seed=42, samples=5000):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(values, size=len(values), replace=True).mean()
                      for _ in range(samples)])
    return tuple(float(x) for x in np.quantile(means, [0.025, 0.975]))

def analyze(raw_csv: str | Path, baseline: str = "baseline") -> Path:
    raw_csv = Path(raw_csv)
    with raw_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("Empty experiment results")
    keys = [(r["image_id"], r["method"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate image/method pairs")
    reference = {r["image_id"]: r for r in rows if r["method"] == baseline}
    if not reference:
        raise ValueError(f"Baseline '{baseline}' not found")
    methods = sorted({r["method"] for r in rows if r["method"] != baseline})
    output = []
    for method in methods:
        selected = [r for r in rows if r["method"] == method]
        if set(r["image_id"] for r in selected) != set(reference):
            raise ValueError(f"Method {method} has missing or additional images")
        for metric, direction in METRICS.items():
            diffs = np.array([direction * (float(r[metric]) -
                             float(reference[r["image_id"]][metric]))
                             for r in selected], dtype=float)
            finite = diffs[np.isfinite(diffs)]
            if not len(finite):
                continue
            lo, hi = bootstrap_ci(finite)
            output.append({
                "method": method, "baseline": baseline, "metric": metric,
                "direction": "positive = improvement", "n_images": len(finite),
                "mean_improvement": float(finite.mean()),
                "median_improvement": float(np.median(finite)),
                "std_improvement": float(finite.std(ddof=1)) if len(finite)>1 else 0.0,
                "fraction_improved": float((finite>0).mean()),
                "ci95_low": lo, "ci95_high": hi,
            })
    result = raw_csv.parent / "paired_summary.csv"
    if output:
        with result.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(output[0]))
            writer.writeheader()
            writer.writerows(output)
    return result
