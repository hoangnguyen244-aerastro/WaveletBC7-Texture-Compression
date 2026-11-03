# WaveletBC7 Texture Compression — Research Framework (v1)

Research goal: **test whether fixed/adaptive Wavelet preprocessing improves decoded BC7 texture quality** using paired, reproducible experiments. No improvement is presumed.

## Components
- `src/wavelet.py`: existing wavelet filtering implementation.
- `src/wavelet_bc7/codec.py`: existing Microsoft DirectXTex texconv wrapper.
- `src/metrics.py`: existing PSNR, SSIM, MAE.
- `src/wavelet_bc7/research.py`: experiment runner, hashes, environment capture, edge MAE and artifact export.
- `src/wavelet_bc7/analysis.py`: per-image paired comparisons with percentile bootstrap intervals.
- `scripts/run_research.py`: CLI runner.
- `docs/experiment_protocol.md`: methods and limitations.

## Recommended Windows installation (Python 3.11 x64)

After cloning, run from PowerShell in the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

This creates the project-local `.venv`, installs all dependencies including PySide6 and pytest, validates the environment, and runs tests. Read [Windows installation guide](docs/windows_setup.md). Virtual environments are not copied between computers; rerun setup after cloning.

## Manual installation (Python 3.11+)
```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```
Download a trusted compatible `texconv.exe` separately (not bundled), for example from Microsoft's DirectXTex release.

## Run the pilot
```bash
python -m scripts.run_research --config configs/pilot.json
```
Runs three pre-existing albedo textures, three methods, CPU BC7 encoding, then writes:
- `results/experiments/pilot_001/raw_results.csv`
- `results/experiments/pilot_001/paired_summary.csv`
- `results/experiments/pilot_001/config.json`
- `results/experiments/pilot_001/environment.json`
- `results/experiments/pilot_001/artifacts/` with PNG/DDS outputs

The run refuses to overwrite an existing nonempty output directory. To repeat a run, change `output_directory` in a copied config. No results are fabricated or committed.

## Generate thesis tables and plots
After a successful experiment:
```bash
python -m scripts.generate_report results/experiments/pilot_001
```
Creates `report.md` and PNG/SVG paired-comparison charts in `figures/`. These are computed from real `paired_summary.csv` values; no example numbers are substituted.

## Tests
```bash
python -m pytest tests/test_research.py
```

## Scientific precautions
The pilot data are for functional testing only, not for a defensible thesis conclusion. Expand to independently sourced textures and grouped splits; freeze the test configuration before evaluating it. Report quality regressions alongside improvements. BC7 is fixed-rate for fixed dimensions and mip levels, so output size reduction is NOT the stated goal.

## Future work
Statistical significance on a locked test set, cluster bootstrap by material, repeated timing runs, chart/report generator, normal/roughness-specific metrics, API layer. This branch is the first working research foundation, not a finished thesis with validated empirical results.
