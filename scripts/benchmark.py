"""Run reproducible fixed-rate BC7 comparisons on a directory of PNGs."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wavelet_bc7.pipeline import evaluate


def benchmark(input_dir, output_dir, strengths, backend, texconv, wavelet="haar"):
    images = sorted(Path(input_dir).rglob("*.png"))
    if not images:
        raise ValueError(f"No PNG files found in {input_dir}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for image in images:
        configurations = [("identity", 0.0)] + [
            (mode, strength) for mode in ("fixed", "adaptive") for strength in strengths
        ]
        for mode, strength in configurations:
            # Separate each run's outputs, including duplicate filenames in subfolders.
            relative = image.relative_to(input_dir)
            run_dir = out / relative.parent / relative.stem / mode / f"{strength:g}"
            result = evaluate(image, run_dir, mode, strength, wavelet, backend, texconv)
            result["split"] = Path(input_dir).name
            rows.append(result)
            print(f"{image.name}: {mode} {strength:g} PSNR={result['psnr_db']:.3f}")
    csv_path = out / "benchmark.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "experiment.json").write_text(
        json.dumps({"input_dir": str(input_dir), "strengths": strengths,
                    "backend": backend, "wavelet": wavelet}, indent=2), encoding="utf-8")
    return csv_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="outputs/benchmark")
    parser.add_argument("--strengths", type=float, nargs="+", default=[1, 2, 4, 8])
    parser.add_argument("--backend", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--texconv", default="tools/texconv.exe")
    parser.add_argument("--wavelet", default="haar")
    args = parser.parse_args()
    print(benchmark(args.input, args.output, args.strengths, args.backend,
                    args.texconv, args.wavelet))
