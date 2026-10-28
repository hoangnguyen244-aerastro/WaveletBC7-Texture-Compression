
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def plot_report(csv_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)

    required = {
        "image", "mode", "psnr_db",
        "ssim", "preprocessing_ms",
        "encode_ms",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing CSV columns: {missing}"
        )

    summary = (
        df.groupby("mode", as_index=False)
        .agg(
            mean_psnr=("psnr_db", "mean"),
            mean_ssim=("ssim", "mean"),
            mean_pre_ms=("preprocessing_ms", "mean"),
            mean_encode_ms=("encode_ms", "mean"),
            samples=("image", "nunique"),
        )
    )

    summary.to_csv(
        output_dir / "summary.csv",
        index=False,
    )

    fig, axes = plt.subplots(
        1, 3, figsize=(14, 4)
    )

    plots = [
        ("mean_psnr", "PSNR (dB)"),
        ("mean_ssim", "SSIM"),
        ("mean_pre_ms", "Preprocessing (ms)"),
    ]

    for ax, (column, title) in zip(axes, plots):
        ax.bar(summary["mode"], summary[column])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(
        output_dir / "benchmark_summary.png",
        dpi=180,
    )
    plt.close(fig)

    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument(
        "--output", default="outputs/reports"
    )
    args = parser.parse_args()

    plot_report(args.csv_path, args.output)
