# Dataset120 V2: reproducible experiment plan (2026-11-17)

## Current evidence and STOP conditions
Git contains exactly 120 PNG paths under resources/textures/train/albedo: Brick, Fabric, Metal, Organic, Stone and Wood, 20 each. **This does not establish 120 valid 1024x1024 RGB images.** The previous GitHub Actions run 44061736174 failed at dataset validation. Its log includes RGBA images and wrong dimensions (e.g. Fabric_07 = 1024x1021, Fabric_12 and Fabric_14 = 1023x1024). Provenance is missing. **Do not report a 120-image independent test result yet.**

Do not delete the originals, historic pilot data, previous branches or test artifacts. The old failing pilot workflow was removed only from this new working branch.

## Stage A — audit and decide the dataset policy
1. Select branch experiment/dataset120-v2-exploratory in GitHub Actions.
2. Run workflow "Dataset120 audit and exploratory BC7 experiment" with run_exploratory=false (the push already triggers the audit).
3. Download dataset120-audit artifact. Read every item in validation_report.json.
4. Decide whether to exclude nonconforming images or make a **separately versioned normalized derivative dataset**. Do not silently resize/crop, flatten alpha or change color space. If flattening RGBA, explicitly document alpha treatment and inspect alpha transparency. If resizing, document interpolation and retain originals. Changes alter the scientific input and must be consistent across all methods.
5. Provide verifiable source URL, license and source_group_id for each texture in datasets/provenance.csv. Do not use fake IDs or pretend different crops are independent. If you cannot verify provenance, label the experiment exploratory.

## Stage B — exploratory functionality (NOT a final thesis result)
The optional workflow_dispatch input run_exploratory=true generates a 120-row manifest, then compares identity BC7, fixed strength=4 and adaptive strength=4 for all images. It writes paired PSNR, SSIM, MAE, edge MAE, timings, DDS sizes and reports. The runner currently converts RGBA to RGB and allows non-1024 sizes; therefore these exploratory results **do not pass the strict dataset protocol** and must not be presented as validated results. Keep the output artifact, original run config, source hashes, and encoder SHA256.

The generator may be used locally:
```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_dataset120_exploratory
.\.venv\Scripts\python.exe -m scripts.run_research --config results/experiments/dataset120_exploratory/exploratory_3methods.json
.\.venv\Scripts\python.exe -m scripts.generate_report results/experiments/dataset120_exploratory/comparison_results
```
The same generator with --sweep creates a separate 9-arm exploratory config: baseline + four fixed and four adaptive strengths (0.5,1,2,4). Do not use the 9-arm results as a held-out test.

## Stage C — defensible thesis experiment (after source audit)
1. Create verified datasets/provenance.csv with image_id,source_group_id,source_url,license. Run `python -m scripts.validate_dataset --root resources/textures/train/albedo --provenance datasets/provenance.csv --make-splits` **only when all images meet the selected strict RGB/dimension policy**. This creates datasets/integration/manifest_v2.csv with grouped splits, approximately 60/20/20 within each material.
2. Freeze dataset version, hashes, wavelet method, texconv SHA256, BC7_UNORM_SRGB, mip count=1, CPU backend, color-space handling and preprocessing policy.
3. On **train**, explore fixed/adaptive strength grid and optionally wavelet family (Haar, db2, db4) only after adding wavelet as an explicit method/config field; current runner hardcodes Haar by default. Do not claim db2/db4 were tested.
4. On **validation**, choose one fixed configuration and one adaptive configuration using a predeclared primary metric (e.g. paired PSNR delta), with SSIM/edge MAE as secondary endpoints. Lock the configuration.
5. Run **held-out test once**: baseline BC7, selected fixed Wavelet+BC7, selected adaptive Wavelet+BC7, on identical images and codec settings. Never optimize on test.
6. Report per-image paired differences, mean, median, distribution, improvement fraction, per-material results, confidence intervals grouped by independent source_group_id (not merely by individual crops), failure examples, and separate preprocess/encode/decode times. Treat timing as exploratory unless warmed up and repeated.
7. The current analysis bootstrap resamples images, not source groups. Implement grouped inference before any thesis-grade significance claim. BC7 fixed-rate means no bitrate reduction claim at fixed resolution/mips.

## Required final outputs
- dataset audit and provenance report; immutable split manifest; dataset source hashes
- exact configuration and encoder SHA256, environment and commit
- raw_results.csv, paired_summary.csv, per-material summary, grouped confidence intervals
- plots of per-material PSNR/SSIM/edge-MAE differences, representative positive and negative images
- separate discussion of limitations and negative outcomes

**Never manufacture metric values or present CI from a 3-image pilot as proof.**
