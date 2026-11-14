"""BC7 baseline error diagnostics from real experiment artifacts.

Usage:
    python -m scripts.analyze_bc7_errors results/experiments/sweep_v1_001

Reads the ORIGINAL texture from the recorded manifest and the decoded baseline
PNG. Does not run texconv or alter the encoder, inputs, or measurements.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pywt
from PIL import Image
from scipy.ndimage import sobel

from src.wavelet_bc7.research import load_manifest

RGB_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def block_errors(original: np.ndarray, decoded: np.ndarray, block_size: int = 4) -> np.ndarray:
    """Per-block RGB mean absolute error; edge blocks may be smaller."""
    if block_size < 1:
        raise ValueError("block_size must be positive")
    if original.shape != decoded.shape or original.ndim != 3 or original.shape[2] != 3:
        raise ValueError("Expected matching HxWx3 images")
    absolute = np.abs(original.astype(np.float64) - decoded.astype(np.float64))
    height, width = absolute.shape[:2]
    result = np.empty(((height + block_size - 1) // block_size,
                       (width + block_size - 1) // block_size), dtype=np.float64)
    for y in range(result.shape[0]):
        for x in range(result.shape[1]):
            tile = absolute[y * block_size:(y + 1) * block_size,
                            x * block_size:(x + 1) * block_size]
            result[y, x] = float(tile.mean())
    return result


def edge_region_errors(original: np.ndarray, decoded: np.ndarray) -> dict:
    """Partition pixels by original luminance Sobel magnitude (top quartile)."""
    rgb = original.astype(np.float64)
    luminance = rgb @ RGB_WEIGHTS
    strength = np.hypot(sobel(luminance, axis=0), sobel(luminance, axis=1))
    cutoff = float(np.percentile(strength, 75))
    # Uniform images contain no meaningful edges: report an empty edge region.
    edge_mask = (strength > 0) & (strength >= cutoff)
    abs_error = np.abs(rgb - decoded.astype(np.float64)).mean(axis=2)
    flat_mask = ~edge_mask
    return {
        "edge_pixel_fraction": float(edge_mask.mean()),
        "edge_mae": float(abs_error[edge_mask].mean()) if edge_mask.any() else None,
        "nonedge_mae": float(abs_error[flat_mask].mean()) if flat_mask.any() else None,
        "edge_mask": edge_mask,
    }


def wavelet_residual_energy(original: np.ndarray, decoded: np.ndarray, wavelet: str = "haar",
                            level: int = 2) -> dict:
    """Energy per detail subband of signed luminance reconstruction residual."""
    if level < 1:
        raise ValueError("level must be >= 1")
    residual = (original.astype(np.float64) - decoded.astype(np.float64)) @ RGB_WEIGHTS
    maximum = pywt.dwt_max_level(min(residual.shape), pywt.Wavelet(wavelet).dec_len)
    actual = min(level, maximum)
    if actual < 1:
        return {}
    coeffs = pywt.wavedec2(residual, wavelet, level=actual, mode="symmetric")
    result = {f"A{actual}": float(np.mean(np.square(coeffs[0])))}
    # coeffs[1] corresponds to coarsest detail level.
    for index, (c_h, c_v, c_d) in enumerate(coeffs[1:]):
        current_level = actual - index
        for label, arr in zip(("H", "V", "D"), (c_h, c_v, c_d)):
            result[f"{label}{current_level}"] = float(np.mean(np.square(arr)))
    return result


def _heatmap(data: np.ndarray, path: Path, title: str, label: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    artist = ax.imshow(data, cmap="magma", interpolation="nearest", vmin=0)
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.colorbar(artist, ax=ax, label=label)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _wavelet_chart(energies: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(energies), list(energies.values()))
    ax.set_ylabel("Mean squared coefficient magnitude")
    ax.set_title("Signed luminance residual: wavelet subband energy")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def analyze_experiment(experiment_dir: str | Path, block_size: int = 4) -> Path:
    root = Path(experiment_dir).resolve()
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    manifest_path = Path(config["dataset_manifest"])
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()
    entries = load_manifest(manifest_path, config["split"])
    with (root / "raw_results.csv").open(newline="", encoding="utf-8-sig") as handle:
        raw = list(csv.DictReader(handle))
    baselines = [r for r in raw if r["mode"] == "identity"]
    by_id = {r["image_id"]: r for r in baselines}
    if len(by_id) != len(baselines) or set(by_id) != {r["image_id"] for r in entries}:
        raise ValueError("Baseline results must contain exactly one row per manifest image")

    out = root / "bc7_error_analysis"
    out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for entry in entries:
        image_id = entry["image_id"]
        baseline = by_id[image_id]
        source = (manifest_path.parent / entry["path"]).resolve()
        if "source_sha256" in baseline and sha256(source) != baseline["source_sha256"]:
            raise ValueError(f"Original image changed since experiment: {image_id}")
        decoded_path = root / "artifacts" / f"{image_id}_{baseline['method']}" / "decoded.png"
        if not decoded_path.is_file():
            raise FileNotFoundError(f"Missing baseline decoded image: {decoded_path}")
        with Image.open(source) as im:
            original = np.asarray(im.convert("RGB"), dtype=np.uint8)
        with Image.open(decoded_path) as im:
            decoded = np.asarray(im.convert("RGB"), dtype=np.uint8)
        if original.shape != decoded.shape:
            raise ValueError(f"Image dimensions mismatch: {image_id}")

        absolute = np.abs(original.astype(np.float64) - decoded.astype(np.float64))
        pixel_mae = absolute.mean(axis=2)
        blocks = block_errors(original, decoded, block_size)
        regions = edge_region_errors(original, decoded)
        wavelet = wavelet_residual_energy(original, decoded)
        folder = out / image_id
        folder.mkdir(exist_ok=True)
        _heatmap(pixel_mae, folder / "pixel_error.png", "BC7 baseline: pixel RGB MAE", "MAE (0–255)")
        _heatmap(blocks, folder / "block_error.png", f"BC7 baseline: {block_size}x{block_size} block MAE", "MAE (0–255)")
        _wavelet_chart(wavelet, folder / "wavelet_residual_energy.png")
        # Numeric arrays are preserved so the figures are not the only evidence.
        np.save(folder / "pixel_error.npy", pixel_mae.astype(np.float32))
        np.save(folder / "block_error.npy", blocks.astype(np.float32))
        np.save(folder / "edge_mask.npy", regions["edge_mask"])
        record = {
            "image_id": image_id, "width": original.shape[1], "height": original.shape[0],
            "baseline_method": baseline["method"], "block_size": block_size,
            "mean_pixel_mae": float(pixel_mae.mean()),
            "mean_block_mae": float(blocks.mean()),
            "p95_block_mae": float(np.percentile(blocks, 95)),
            "max_block_mae": float(blocks.max()),
            "edge_pixel_fraction": regions["edge_pixel_fraction"],
            "edge_region_mae": regions["edge_mae"],
            "nonedge_region_mae": regions["nonedge_mae"],
            **{f"energy_{name}": value for name, value in wavelet.items()},
        }
        (folder / "metrics.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        summaries.append(record)

    path = out / "error_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    report = [
        "# BC7 baseline error diagnostics",
        "",
        f"Experiment: {root.name}; images: {len(summaries)}; block size: {block_size}.",
        "All errors are computed against the ORIGINAL texture, not the preprocessed PNG.",
        "Wavelet energies are descriptive mean squared coefficients of signed luminance residuals,",
        "not a proof that changing a particular subband will improve BC7.",
        "Edge pixels are selected using the top quartile of nonzero original-luminance Sobel strength;",
        "flat images have no edge pixels. Edge/nonedge regions are complementary.",
        "For partial edge blocks, mean_block_mae is unweighted; mean_pixel_mae is pixel-weighted.",
        "",
        "| Image | Pixel MAE | P95 block MAE | Edge MAE | Nonedge MAE |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summaries:
        fmt = lambda v: "N/A" if v is None else f"{v:.4f}"
        report.append(f"| {row['image_id']} | {row['mean_pixel_mae']:.4f} | "
                      f"{row['p95_block_mae']:.4f} | {fmt(row['edge_region_mae'])} | "
                      f"{fmt(row['nonedge_region_mae'])} |")
    report += ["", "These exploratory pilot diagnostics do not establish causal improvement.",
               "Use separate validation and held-out test datasets for V2 model selection.", ""]
    (out / "error_report.md").write_text("\n".join(report), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--block-size", type=int, default=4)
    args = parser.parse_args()
    print("BC7 error summary:", analyze_experiment(args.experiment_dir, args.block_size))


if __name__ == "__main__":
    main()
