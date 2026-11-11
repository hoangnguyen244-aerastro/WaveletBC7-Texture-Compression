# BC7 Error Analysis — Windows 11 and thesis protocol

## Goal

Characterize **where and at which spatial frequencies the standard BC7 baseline loses information** before proposing a codec-aware Wavelet V2. This is a diagnostic tool, not an implementation or proof of V2.

The tool analyzes the **original texture versus the decoded BC7 baseline** from a completed V1 parameter sweep. It never compares the baseline against a preprocessed input, and it never reruns texconv.

## Windows 11 steps

1. In GitHub Desktop, **Fetch origin**, then switch to branch `analysis/bc7-error-diagnostics-v1`. This branch contains the earlier V1 sweep implementation.
2. Open PowerShell in the repository root. The project-local Python 3.11 environment must already be installed.
3. Run:

```powershell
cd "D:\Hoang-Data\Git_Project\WaveletBC7-Texture-Compression"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.analyze_bc7_errors results/experiments/sweep_v1_001
```

If the `results/experiments/sweep_v1_001` directory does not exist on your machine, run the V1 sweep first using `configs/sweep_v1.json` and `scripts.run_research`. The error-analysis command does **not** require a second BC7 encoding run.

The existing sweep directory must contain `config.json`, `raw_results.csv`, and the `artifacts/<image_id>_baseline/decoded.png` files. The original image files must remain at the paths recorded in the dataset manifest. Original-image SHA256 hashes are checked against the recorded sweep rows where available.

## Outputs

Under `results/experiments/sweep_v1_001/bc7_error_analysis/`:

- `error_summary.csv`: one row per texture with mean pixel MAE, mean/p95/max BC7 4×4 block MAE, edge/nonedge MAE, and Wavelet residual energy per band.
- `error_report.md`: short descriptive table and methodological caveats.
- `<image_id>/pixel_error.png`: per-pixel RGB mean absolute error heatmap.
- `<image_id>/block_error.png`: 4×4 BC7-block mean RGB absolute error heatmap.
- `<image_id>/wavelet_residual_energy.png`: Haar two-level subband mean squared energy of **signed luminance residual** (original minus decoded).
- `<image_id>/pixel_error.npy`, `block_error.npy`, `edge_mask.npy`: numerical arrays for subsequent reproducible analyses.
- `<image_id>/metrics.json`: per-image numeric summary.

The default block size is 4, matching BC7 block dimensions. The optional `--block-size 4` flag allows changing the aggregation size for exploratory comparisons; it does not change BC7 encoding.

## Metric definitions and limitations

- Pixel error: `mean_c |I(y,x,c) - I_BC7(y,x,c)|` in 8-bit RGB units.
- Block error: mean pixel error over each non-overlapping 4×4 block. Boundary blocks may be smaller for nonmultiples of four. `mean_block_mae` is unweighted when block sizes differ; `mean_pixel_mae` is pixel-weighted.
- Edge mask: upper quartile of the original-image luminance Sobel magnitude, excluding zero-gradient pixels. Flat images have an empty edge region; the nonedge mask is its complement. This is a diagnostic partition, not a perceptual metric.
- Wavelet frequency analysis: 2-level Haar decomposition of **signed luma reconstruction residual**, reported as mean squared coefficients by approximation/detail band. These are not Fourier frequencies or independently normalized energy shares; compare carefully across levels.
- The analysis assumes RGB textures, consistent color handling and the same decoded BC7 profile used in the experiment. Normal maps and roughness require separate domain-aware analyses.
- High error in a block does not imply a specific BC7 mode/partition choice; the tool does not parse BC7 bitstream internals.
- Pilot size is only three albedo textures. Use this to formulate V2 hypotheses, not to claim statistically significant generalization.

## Next research step

Use high-error regions and wavelet bands to formulate **testable** V2 preprocessing candidates. Select hyperparameters on a material-grouped validation dataset, then evaluate once on held-out test images. Track quality improvements and preprocessing/encoding costs.

For discussion of results, share `error_summary.csv`, `error_report.md` and representative `pixel_error.png` / `block_error.png` images.
