"""Summarize benchmark measurements by mode and threshold."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_report(csv_path, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)
    required = {"image", "mode", "strength", "psnr_db", "ssim",
                "mae", "preprocessing_ms", "encode_ms"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Benchmark CSV has no rows")
    summary = (df.groupby(["mode", "strength"], as_index=False)
               .agg(mean_psnr=("psnr_db", "mean"),
                    mean_ssim=("ssim", "mean"),
                    mean_mae=("mae", "mean"),
                    mean_pre_ms=("preprocessing_ms", "mean"),
                    mean_encode_ms=("encode_ms", "mean"),
                    samples=("image", "nunique")))
    summary.to_csv(output / "summary.csv", index=False)
    labels = [f"{m} {s:g}" for m, s in zip(summary["mode"], summary["strength"])]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, column, title in zip(axes,
        ["mean_psnr", "mean_ssim", "mean_pre_ms"],
        ["PSNR (dB)", "SSIM", "Preprocessing (ms)"]):
        ax.bar(labels, summary[column])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "benchmark_summary.png", dpi=180)
    plt.close(fig)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--output", default="outputs/reports")
    args = parser.parse_args()
    print(plot_report(args.csv_path, args.output).to_string(index=False))
