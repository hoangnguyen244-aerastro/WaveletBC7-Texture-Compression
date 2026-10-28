# WaveletBC7 Texture Compression

Research project comparing **BC7 at fixed bitrate** with and without wavelet preprocessing.

## Setup (Python 3.11)

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

BC7 encoding and decoding require Microsoft's **DirectXTex texconv.exe**, installed locally at `tools/texconv.exe` or provided by an explicit path. The executable is not distributed with this repository.

## Current code

- `wavelet_bc7.preprocess.wavelet_preprocess`: identity, fixed-threshold and edge-adaptive wavelet preprocessing for uint8 RGB.
- `wavelet_bc7.metrics.measure`: PSNR, SSIM and MAE on encoded sRGB channel values.
- `wavelet_bc7.codec.Texconv`: BC7 encode/decode via external texconv.
- `wavelet_bc7.dds.inspect_bc7_dds`: validation of single-mip 2D BC7 DDS.

**Important:** BC7 stores 16 bytes per 4×4 block, so preprocessing does not reduce BC7 payload size at the same dimensions and mip count. Evaluate decoded image quality at fixed bitrate.

The Windows texconv integration still requires a local end-to-end validation before benchmark results can be reported. Dataset splits and reproducible batch benchmark are planned in subsequent commits.
