# V1 parameter sweep — Windows 11 (Python 3.11)

This experiment is based on `feature/research-framework-v1`, **not** on the older `main` branch. It keeps the V1 Wavelet implementation and BC7 codec unchanged.

## Experimental matrix

- Dataset: three existing pilot **albedo RGB** images (Brick, Metal, Wood) in `datasets/manifest.csv`.
- Baseline: identity preprocessing + BC7.
- Fixed Wavelet: strengths `0.25, 0.5, 1, 2, 4, 8`.
- Adaptive Wavelet: same six strengths.
- 13 variants × 3 images = **39 BC7 encodes**, each with its own decoded image.
- CPU backend; same texconv executable and BC7 settings for every variant.
- No new measurements are included in Git: the user must run the actual encoder on Windows.

## Run on Windows 11

**First**, in GitHub Desktop fetch the remote and select the new branch `experiment/v1-parameter-sweep` (Branch → Choose a branch). This branch is based on `feature/research-framework-v1`. Do **not** switch to `main` for the experiment.

Open PowerShell and run:

```powershell
cd "D:\Hoang-Data\Git_Project\WaveletBC7-Texture-Compression"

# Verify your project-local environment; only install once per machine.
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pytest -q

# Confirm texconv exists (already installed on your machine).
Test-Path .\tools\texconv.exe

# Run the 39-encode pilot. This can take several minutes.
.\.venv\Scripts\python.exe -m scripts.run_research --config configs/sweep_v1.json

# Export paired per-method metrics, plots, and the V1 sweep report.
.\.venv\Scripts\python.exe -m scripts.analyze_sweep results/experiments/sweep_v1_001
```

If `Test-Path` returns `False`, copy your trusted `texconv.exe` into `tools\texconv.exe` or change `texconv_executable` in the JSON config to its full path. Do not commit the executable.

The existing environment **does not need reinstalling** every time you run an experiment. If the local `.venv` is missing, run the repository's `setup_windows.ps1` once.

## Output files

All actual measured outputs are saved locally under `results/experiments/sweep_v1_001/`:

| File | Description |
| --- | --- |
| `raw_results.csv` | 39 measured image–method rows with PSNR, SSIM, MAE, edge MAE, runtime, DDS bytes |
| `paired_summary.csv` | Paired comparisons for all 12 nonbaseline methods |
| `sweep_summary.csv` | 12 strength/mode rows with mean metric improvements and improvement fractions |
| `sweep_report.md` | Pilot analysis, ranking by mean PSNR change and limitations |
| `figures/psnr_strength.png` | Mean ΔPSNR versus strength |
| `figures/psnr_strength.svg` | Vector version of the same plot |
| `config.json`, `environment.json` | Exact experiment configuration, environment and texconv SHA-256 |
| `artifacts/` | Intermediate PNG, compressed DDS, and decoded PNG per method |

**Important:** The experiment runner refuses to overwrite a nonempty experiment directory. For another run, edit `output_directory` in a copied config (for example `sweep_v1_002`); never delete the previous data accidentally.

## Interpretation

- ΔPSNR and ΔSSIM: higher is better.
- Improvement in MAE and edge MAE: positive means error decreased (the analysis flips the sign).
- A configuration with mean ΔPSNR ≤ 0 did not improve PSNR over BC7 on this pilot.
- At fixed image dimensions and mip levels, BC7 is fixed-rate; do **not** claim that Wavelet preprocessing reduces DDS size.
- The pilot has only three images. Choose parameters on a separate **validation** split, then test once on an independent held-out **test** split. The best pilot setting is exploratory, not a thesis-level conclusion.
- The synthetic unit-test fixtures check calculations and file generation; they are **not** actual compression results.

To send results for thesis analysis, attach `raw_results.csv`, `paired_summary.csv`, `sweep_summary.csv`, and `sweep_report.md`. Keep the original files unmodified.
