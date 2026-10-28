
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)

from src.wavelet import wavelet_preprocess
from src.bc7 import Texconv
from src.metrics import measure


def run(input_file, mode, strength, out_dir, texconv):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(input_file) as img:
        rgba = np.asarray(
            img.convert("RGBA"), dtype=np.uint8
        )

    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    processed = wavelet_preprocess(
        rgb, mode=mode, strength=strength
    )

    output_rgba = np.dstack([processed, alpha])

    stem = Path(input_file).stem
    tag = f"{stem}_{mode}_{strength:g}"

    pre_png = out_dir / f"{tag}_preprocessed.png"
    dds = out_dir / f"{tag}.dds"
    decoded_png = out_dir / f"{tag}_decoded.png"

    Image.fromarray(
        output_rgba, mode="RGBA"
    ).save(pre_png)

    codec = Texconv(texconv)
    codec.encode_bc7(pre_png, dds)
    codec.decode_png(dds, decoded_png)

    with Image.open(decoded_png) as img:
        decoded = np.asarray(
            img.convert("RGB"), dtype=np.uint8
        )

    scores = measure(rgb, decoded)

    print(f"Preprocessed PNG: {pre_png}")
    print(f"BC7 DDS:          {dds}")
    print(f"Decoded PNG:      {decoded_png}")
    print(f"DDS size:         {dds.stat().st_size} bytes")
    print(f"PSNR:             {scores['psnr_db']:.3f} dB")
    print(f"SSIM:             {scores['ssim']:.5f}")
    print(f"MAE:              {scores['mae']:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument(
        "--mode",
        choices=["identity", "fixed", "adaptive"],
        default="adaptive",
    )
    parser.add_argument(
        "--strength", type=float, default=4.0
    )
    parser.add_argument(
        "--output", default="outputs/demo"
    )
    parser.add_argument(
        "--texconv", default="tools/texconv.exe"
    )
    args = parser.parse_args()

    run(
        args.input,
        args.mode,
        args.strength,
        args.output,
        args.texconv,
    )
