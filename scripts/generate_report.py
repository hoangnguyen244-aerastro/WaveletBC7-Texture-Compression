"""Export thesis-ready comparison tables and charts from real experiment CSVs."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def generate(experiment_dir):
    root = Path(experiment_dir)
    input_csv = root / "paired_summary.csv"
    if not input_csv.exists():
        raise FileNotFoundError(f"Run the experiment and paired analysis first: {input_csv}")
    with input_csv.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("No paired results available")
    figures = root / "figures"
    figures.mkdir(exist_ok=True)
    lines = ["# Experiment report", "",
             "Data: `raw_results.csv`; comparison: `paired_summary.csv`.",
             "Positive improvements indicate better quality; metrics MAE and edge MAE were sign-inverted.",
             "", "| Method | Metric | N | Mean improvement | 95% bootstrap CI | Fraction improved |",
             "|---|---|---:|---:|---|---:|"]
    for row in rows:
        lines.append("| {method} | {metric} | {n_images} | {mean_improvement:.5f} | [{ci95_low:.5f}, {ci95_high:.5f}] | {fraction_improved:.1%} |".format(
            **{**row, **{k: float(row[k]) for k in
                           ("mean_improvement","ci95_low","ci95_high","fraction_improved")}}))
    for metric in ("psnr_db", "ssim", "mae", "edge_mae"):
        group = [r for r in rows if r["metric"] == metric]
        if not group:
            continue
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [r["method"] for r in group]
        means = [float(r["mean_improvement"]) for r in group]
        lower = [max(0, m-float(r["ci95_low"])) for m,r in zip(means,group)]
        upper = [max(0, float(r["ci95_high"])-m) for m,r in zip(means,group)]
        ax.bar(labels, means)
        ax.errorbar(labels, means, yerr=[lower, upper], fmt="none", capsize=4)
        ax.axhline(0, linewidth=1, linestyle="--")
        ax.set_ylabel(f"Improvement in {metric} (positive = better)")
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        fig.savefig(figures / f"paired_{metric}.png", dpi=300)
        fig.savefig(figures / f"paired_{metric}.svg")
        plt.close(fig)
        lines.extend(["", f"## {metric}", f"![{metric}](figures/paired_{metric}.png)"])
    (root / "report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return root / "report.md"

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("experiment_dir")
    print(generate(p.parse_args().experiment_dir))
