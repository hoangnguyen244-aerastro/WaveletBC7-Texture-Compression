# Dataset integration and validation (Windows 11)

This branch adds a **non-destructive** inventory/validation pipeline for the 120 new albedo textures in `resources/textures/train/albedo/`. The previous `datasets/manifest.csv` (three pilot images), V1 sweep and BC7 error analysis remain unchanged.

## 1. Validate local images

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -vv --tb=short
.\.venv\Scripts\python.exe -m scripts.validate_dataset --root resources/textures/train/albedo
```

The validator checks expected 6×20 names, PNG readability and full decode, 1024×1024 resolution, 8-bit RGB, exact duplicate SHA-256, and presence of provenance metadata. It writes `datasets/integration/inventory.csv` and `datasets/integration/validation_report.json`. **Warnings** about missing provenance are expected until you supply it. **Errors** cause a nonzero exit code.

The validator does not move or modify images. A GitHub tree listing confirms file names, not image dimensions, color mode, source authenticity or license; these checks must be run locally.

## 2. Add verifiable provenance

Create `datasets/provenance.csv` with the following header:

```csv
image_id,source_group_id,source_url,license
```

Provide one row for **every** image, e.g. `brick_01`. `source_group_id` must identify the **underlying source material**, not an individual crop or resize. All derivatives/crops of the same original material must have the **same** group ID. Use a real source URL and the verified license, not placeholders. Avoid making up provenance.

If you do not know which images derive from the same material, first investigate and document their origin. Exact hash matching does not detect resizes, crops, recompression or near-duplicates.

## 3. Generate independent splits only after provenance review

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_dataset --root resources/textures/train/albedo --provenance datasets/provenance.csv --make-splits
```

On success, creates `datasets/integration/manifest_v2.csv`, which is **compatible with the existing research runner** (the first four required columns are preserved). All images in a source group are assigned to the same split. Train/validation/test are targeted at 60/20/20 **per material**, but exact ratios can differ when groups have multiple images. At least three independent source groups per material are required.

**Important:** The images physically remain under `resources/textures/train/albedo/` for backward compatibility, but the `split` column in `manifest_v2.csv` controls their logical research split. Do not assume directory name `train` means all 120 images are assigned to train. Do not choose V2 parameters based on the test split.

To use the new manifest in a future experiment, copy a JSON config, change `dataset_manifest` to `datasets/integration/manifest_v2.csv`, change `split` to `train` or `validation`, and set a **new** `output_directory`. Do not overwrite existing experiment results.

## 4. What the checks do not establish

- Pixel-level integrity, format, dimensions and exact file duplicates are checked locally, **not** by merely listing GitHub files.
- Perceptual near-duplicates and derivative relationships are not automatically detected. Human provenance review is necessary.
- A declared license is not independently verified against the source website.
- A 1024×1024 RGB PNG can still be a lighting-baked preview rather than true albedo. Inspect source material metadata.
- This stage does not perform BC7 encoding or claim any Wavelet V2 quality improvements.

Keep `datasets/integration/` local unless you deliberately decide to publish reports; it is gitignored. Review provenance and any manifest before committing dataset metadata.
