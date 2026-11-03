# Experimental protocol (v1)

## Research question
Does Wavelet preprocessing improve reconstructed albedo RGB texture quality relative to otherwise identical BC7 encoding?

## Design
- Within-image paired comparison: identity→BC7 (baseline), fixed Wavelet→BC7, adaptive Wavelet→BC7.
- Always evaluate the decoded images against the ORIGINAL input, never against the preprocessed input.
- Keep resolution, color space, codec executable SHA256, backend, mip levels, and profile identical.
- Pilot split is used for smoke testing ONLY. Build independent material-grouped train/validation/test splits before any thesis claims.
- Select parameters on validation. Freeze configuration before running held-out test.
- Report failures and negative results, not only images that improve.

## Measurements
PSNR (dB), SSIM, MAE, edge-weighted-region MAE; separated preprocessing, encoding and decoding times; DDS bytes. For MAE metrics, lower is better. For PSNR/SSIM, higher is better.

## Statistics
Pair metrics by image_id, calculate differences per image (adjust signs so positive is improvement), report sample size, mean, median, SD, improvement rate, and image-level bootstrap percentile confidence intervals. For near-duplicate material textures use material-group cluster bootstrap before making inferential claims. A CI is not a proof of causal novelty.

## Known limitations
- BC7 fixed rate: wavelet preprocessing does not inherently reduce output bytes at fixed dimensions/mip levels.
- The pilot corpus contains only three albedo textures and is NOT a research validation dataset.
- Default CPU/GPU profiles may differ; record and pin tool version and options.
- Time benchmarks need warm-up, repeated runs and machine specifications.
- Codec output quality depends on the external texconv binary; obtain it from an official trusted distribution.
- Do not assume an observed improvement until running the pipeline.
- Confirm image reuse rights before redistributing the dataset.
