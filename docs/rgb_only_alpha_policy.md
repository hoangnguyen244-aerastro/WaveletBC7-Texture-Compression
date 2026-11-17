# RGB-only policy for the 120-image Wavelet–BC7 experiment

Original RGB/RGBA PNGs remain untouched. The experiment reads only channels R, G, B from each PNG. Alpha is discarded **without compositing**, is never input to edge detection, Wavelet transform, BC7 encoder, decoded-image metrics or preprocessing time measurements. The encoder receives a temporary RGB PNG; the DDS output is BC7_UNORM_SRGB with the alpha channel not evaluated against the source. The alpha content of original images is **not preserved** in the resulting DDS.

The strict dataset validator currently requires mode RGB and will flag source RGBA files. That validator is intended for RGB-only source datasets and is **not the acceptance criterion** for this RGB-extraction experiment. For the present protocol, acceptance requires: exactly 120 readable PNG files, six categories with 20 images each, 1024x1024 dimensions, input modes RGB or RGBA, and a documented RGB extraction rule. Run `python -m scripts.audit_alpha` for a read-only audit. Do not interpret its nonopaque RGBA count as an experiment failure.

`src/wavelet_bc7/rgb_policy.py::extract_rgb` performs direct HxWx4 -> HxWx3 slicing, not `alpha_composite` or RGBA blending. The `research.py` runner uses this extraction for all methods. Unit test `tests/test_rgb_policy.py` proves that two images with identical RGB and different Alpha yield identical extracted RGB, Wavelet output and image metrics.

Limitations: pixels with zero alpha may contain arbitrary or artistically unintended RGB values. Under this policy those RGB values are still analyzed. This is a deliberate scope choice, not a guarantee of visible-appearance equivalence. Report it in the thesis methodology. The image-level RGB policy is separate from license/provenance and independent source-group split verification.

## Run
```powershell
python -m pytest tests/test_rgb_policy.py -q
python -m scripts.audit_alpha
python -m scripts.prepare_dataset120_exploratory
python -m scripts.run_research --config results/experiments/dataset120_exploratory/exploratory_3methods.json
```
Use fresh output directory if results already exist. Do not treat exploratory results as held-out test measurements.
