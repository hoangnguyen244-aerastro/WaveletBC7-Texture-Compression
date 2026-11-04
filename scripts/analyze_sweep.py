"""Summarize a completed, paired Wavelet–BC7 V1 parameter sweep.

Only reads measured raw_results.csv; never invents experimental results.
Usage: python -m scripts.analyze_sweep results/experiments/sweep_v1_001
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from scripts.plot_sweep import plot

METRICS = ("psnr_db", "ssim", "mae", "edge_mae")
STRENGTHS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
MODES = ("fixed", "adaptive")


def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("No measured rows in raw_results.csv")
    required = {"image_id", "method", "mode", "strength", *METRICS}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")
    return rows


def summarize(raw_csv: str | Path, output_dir: str | Path | None = None) -> tuple[Path, Path]:
    raw_csv = Path(raw_csv)
    output_dir = Path(output_dir) if output_dir else raw_csv.parent
    rows = _read_rows(raw_csv)
    seen = set()
    grouped = defaultdict(dict)
    for row in rows:
        key = (row["image_id"], row["method"])
        if key in seen:
            raise ValueError(f"Duplicate image/method: {key}")
        seen.add(key)
        mode = row["mode"]
        strength = float(row["strength"])
        if mode not in ("identity", *MODES):
            raise ValueError(f"Unexpected mode: {mode}")
        if mode != "identity" and strength not in STRENGTHS:
            raise ValueError(f"Unexpected strength: {strength}")
        grouped[row["image_id"]][(mode, strength)] = row

    expected = {("identity", 0.0)} | {(m, s) for m in MODES for s in STRENGTHS}
    for image_id, methods in grouped.items():
        missing = expected - set(methods)
        extra = set(methods) - expected
        if missing or extra:
            raise ValueError(f"Incomplete sweep for {image_id}: missing={sorted(missing)}, extra={sorted(extra)}")
    n = len(grouped)
    summary = []
    for mode in MODES:
        for strength in STRENGTHS:
            changes = {metric: [] for metric in METRICS}
            for image_id, methods in grouped.items():
                baseline = methods[("identity", 0.0)]
                candidate = methods[(mode, strength)]
                for metric in METRICS:
                    a, b = float(baseline[metric]), float(candidate[metric])
                    if not (math.isfinite(a) and math.isfinite(b)):
                        raise ValueError(f"Non-finite {metric} for {image_id}")
                    # All improvement columns are positive when quality improves.
                    direction = 1 if metric in ("psnr_db", "ssim") else -1
                    changes[metric].append(direction * (b - a))
            record = {"mode": mode, "strength": strength, "n_images": n}
            for metric, values in changes.items():
                record[f"mean_improvement_{metric}"] = sum(values) / n
                record[f"fraction_improved_{metric}"] = sum(x > 0 for x in values) / n
            summary.append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "sweep_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    # Descriptive selection only; never optimize on the held-out test split.
    best = max(summary, key=lambda r: r["mean_improvement_psnr_db"])
    lines = [
        "# Wavelet–BC7 V1: parameter sweep",
        "",
        f"- Images: {n}; paired BC7 baseline + 12 variants per image.",
        "- Data: measured raw_results.csv; improvements compare decoded output against the original image.",
        "- Positive improvement means better quality for all metrics (MAE values are sign-inverted).",
        "- BC7 is fixed-rate at the same dimensions and mip count; file-size reduction is not claimed.",
        "- This pilot is exploratory, not independent validation or statistical proof.",
        "",
        "## Mean PSNR improvement vs baseline (dB)",
        "",
        "| Mode | Strength | Mean ΔPSNR | Fraction improved |",
        "|---|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(f"| {row['mode']} | {row['strength']:g} | {row['mean_improvement_psnr_db']:+.4f} | {row['fraction_improved_psnr_db']:.0%} |")
    lines += [
        "",
        f"Best observed pilot setting by mean ΔPSNR: **{best['mode']} / {best['strength']:g}** ({best['mean_improvement_psnr_db']:+.4f} dB).",
        "",
        "This is a descriptive pilot selection, not evidence of generalization. "
        "Choose hyperparameters on a separate validation split before locked test evaluation.",
        "",
        "See sweep_summary.csv for SSIM, MAE and edge-MAE changes, and figures/psnr_strength.png for the curve.",
        "",
    ]
    report_path = output_dir / "sweep_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    plot(raw_csv)
    return csv_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path, help="Directory with measured raw_results.csv")
    args = parser.parse_args()
    csv_path, report_path = summarize(args.experiment_dir / "raw_results.csv")
    print(f"Sweep summary: {csv_path}")
    print(f"Sweep report: {report_path}")
    print(f"PSNR curve: {args.experiment_dir / 'figures' / 'psnr_strength.png'}")


if __name__ == "__main__":
    main()
