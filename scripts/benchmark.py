
import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)

from src.wavelet import wavelet_preprocess
from src.bc7 import Texconv
from src.metrics import measure


EXTENSIONS = {".png", ".jpg", ".jpeg", ".tga"}


def benchmark(root, output, texconv, strengths):
    root = Path(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    codec = Texconv(texconv)
    rows = []

    files = sorted(
        p for p in root.rglob("*")
        if p.suffix.lower() in EXTENSIONS
    )

    if not files:
        raise RuntimeError(f"No images found in {root}")

    configurations = [("identity", 0.0)]
    configurations += [
        ("fixed", x) for x in strengths
    ]
    configurations += [
        ("adaptive", x) for x in strengths
    ]

    for image_path in files:
        with Image.open(image_path) as img:
            rgba = np.asarray(
                img.convert("RGBA"), dtype=np.uint8
            )

        rgb = rgba[:, :, :3]
        alpha = rgba[:, :, 3]
        h, w = rgb.shape[:2]

        # BC7 requires block-aligned dimensions for
        # this controlled first version of the experiment.
        if w % 4 or h % 4:
            print(f"Skipping non-4-aligned: {image_path}")
            continue

        relative = image_path.relative_to(root)
        sample_id = relative.with_suffix("").as_posix()
        safe_name = sample_id.replace("/", "__")

        for mode, strength in configurations:
            tag = f"{safe_name}_{mode}_{strength:g}"
            sample_dir = output / "artifacts"
            sample_dir.mkdir(exist_ok=True)

            pre_png = sample_dir / f"{tag}.png"
            dds = sample_dir / f"{tag}.dds"
            decoded_png = (
                output / "decoded" / f"{tag}.png"
            )

            start = time.perf_counter()
            processed = wavelet_preprocess(
                rgb, mode=mode, strength=strength
            )
            preprocessing_ms = (
                time.perf_counter() - start
            ) * 1000

            Image.fromarray(
                np.dstack([processed, alpha]),
                mode="RGBA",
            ).save(pre_png)

            start = time.perf_counter()
            codec.encode_bc7(pre_png, dds)
            encode_ms = (
                time.perf_counter() - start
            ) * 1000

            codec.decode_png(dds, decoded_png)

            with Image.open(decoded_png) as img:
                decoded = np.asarray(
                    img.convert("RGB"),
                    dtype=np.uint8,
                )

            scores = measure(rgb, decoded)

            rows.append({
                "image": sample_id,
                "width": w,
                "height": h,
                "mode": mode,
                "strength": strength,
                "psnr_db": scores["psnr_db"],
                "ssim": scores["ssim"],
                "mae": scores["mae"],
                "preprocessing_ms": preprocessing_ms,
                "encode_ms": encode_ms,
                "dds_bytes": dds.stat().st_size,
            })

            print(
                f"{sample_id} | {mode:8} | "
                f"{strength:5.1f} | "
                f"PSNR={scores['psnr_db']:.2f} | "
                f"SSIM={scores['ssim']:.4f}"
            )

    if not rows:
        raise RuntimeError("No eligible images processed")

    report = output / "benchmark.csv"
    with report.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nReport saved: {report}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="resources/textures/test/albedo",
    )
    parser.add_argument(
        "--output", default="outputs/benchmark"
    )
    parser.add_argument(
        "--texconv", default="tools/texconv.exe"
    )
    parser.add_argument(
        "--strengths",
        nargs="+",
        type=float,
        default=[1, 2, 4, 8],
    )
    args = parser.parse_args()

    benchmark(
        args.input,
        args.output,
        args.texconv,
        args.strengths,
    )
