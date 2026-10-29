# WaveletBC7 Research Studio (Windows GUI)

## Start
1. On the `feature/research-framework-v1` branch, run `setup_windows.ps1` once (Python 3.11 x64 required).
2. Double-click `start_studio.bat` in the project folder. No terminal commands are needed for subsequent experiments.
3. In the GUI, confirm `datasets/manifest.csv`, `tools/texconv.exe`, choose split `pilot`, and enter strengths `0.25, 0.5, 1, 2, 4`.
4. Set a NEW output directory for each run; outputs are deliberately not overwritten.
5. Click **Run Sweep**. The compression runs on a worker thread; wait for **Completed** and then select rows to inspect original, preprocessed, decoded and amplified error images.
6. A report and figures are automatically generated from actual data. The **Generate Report** button can regenerate the plots, including `figures/psnr_strength.png` and SVG.

## Scientific interpretation
The colored error view multiplies pixel errors by eight for display only; it is NOT a measurement or true color difference map. The PSNR-strength chart is a descriptive mean paired difference from baseline (positive means improvement). The three-image pilot is only a software validation run: use separate, grouped validation/test splits for any thesis conclusion.

## Limitations
- Progress currently displays running/completed, not percentage. Experiment errors are displayed in a dialog.
- GUI currently processes RGB albedo only; alpha is not evaluated.
- A fresh output directory is needed for each run, including failed/partial runs.
- GUI image previews require the original dataset to remain accessible at the manifest path.
- The quality of results depends on texconv version and configuration; avoid claiming general improvements from pilot results.
