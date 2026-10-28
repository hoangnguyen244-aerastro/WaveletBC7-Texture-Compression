# WaveletBC7 Texture Compression

Research pipeline comparing BC7 encoding at a fixed rate with identity, fixed-threshold and edge-adaptive wavelet preprocessing.

## Install

Python 3.11:

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

Download Microsoft DirectXTex `texconv.exe` separately and place it in `tools/texconv.exe` (or pass `--texconv`). It is not bundled with this repository. The CLI needs Windows for native texconv execution.

## Batch benchmark

```powershell
python scripts/benchmark.py --input resources/textures/train/albedo --output outputs/benchmark --strengths 1 2 4 8 --backend cpu --texconv tools/texconv.exe
python scripts/plot_benchmark.py outputs/benchmark/benchmark.csv --output outputs/reports
```

The benchmark writes per-run PNG and DDS outputs, `benchmark.csv`, and `experiment.json`. The plotter writes `summary.csv` and `benchmark_summary.png`. Each input image is compared against the same original RGB reference. Metrics are PSNR, SSIM and MAE on 8-bit sRGB code values. Runtime measurements include preprocessing, encoding and decoding wall time.

`src/wavelet_bc7/pipeline.py` is the new evaluation API. The original `src/process_texture.py` is retained temporarily during migration; it still uses the legacy codec.

## Scientific constraints

BC7 uses 16 bytes per 4×4 block, so the BC7 payload is fixed for a given image size and mip count. The objective is decoded quality at fixed rate, **not** a smaller BC7 payload.

The current textures are training/demo examples only; see [DATASET.md](DATASET.md). Independent test data, confirmed dataset licensing, and Windows texconv end-to-end validation are still required before making thesis claims.

The codec's `texconv` command-line options must be validated against the locally installed DirectXTex version; CI unit tests do not run the Windows encoder.
