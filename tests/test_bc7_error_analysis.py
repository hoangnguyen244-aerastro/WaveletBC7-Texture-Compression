"""Deterministic synthetic tests; not experimental BC7 quality claims."""
import csv
import json

import numpy as np
import pytest
from PIL import Image

from scripts.analyze_bc7_errors import (
    analyze_experiment, block_errors, edge_region_errors, wavelet_residual_energy,
)


def test_block_error_with_partial_border():
    original = np.zeros((5, 6, 3), dtype=np.uint8)
    decoded = np.full_like(original, 2)
    blocks = block_errors(original, decoded)
    assert blocks.shape == (2, 2)
    assert np.allclose(blocks, 2.0)


def test_identical_image_zero_residual():
    image = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    assert np.all(block_errors(image, image) == 0)
    assert all(v == 0 for v in wavelet_residual_energy(image, image).values())


def test_flat_image_has_no_edge_region():
    image = np.full((8, 8, 3), 128, dtype=np.uint8)
    decoded = np.full_like(image, 126)
    stats = edge_region_errors(image, decoded)
    assert stats["edge_pixel_fraction"] == 0
    assert stats["edge_mae"] is None
    assert stats["nonedge_mae"] == pytest.approx(2)


def _fixture(tmp_path):
    root = tmp_path / "experiment"
    root.mkdir()
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    source = dataset / "image.png"
    Image.fromarray(np.full((8, 8, 3), 100, dtype=np.uint8)).save(source)
    manifest = dataset / "manifest.csv"
    manifest.write_text(
        "image_id,path,split,material_group\nexample,image.png,pilot,synthetic\n",
        encoding="utf-8",
    )
    (root / "config.json").write_text(
        json.dumps({"dataset_manifest": str(manifest), "split": "pilot"}),
        encoding="utf-8",
    )
    with (root / "raw_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["image_id", "method", "mode"])
        writer.writeheader()
        writer.writerow({"image_id": "example", "method": "baseline", "mode": "identity"})
    folder = root / "artifacts" / "example_baseline"
    folder.mkdir(parents=True)
    Image.fromarray(np.full((8, 8, 3), 98, dtype=np.uint8)).save(folder / "decoded.png")
    return root


def test_full_analysis_generates_outputs(tmp_path):
    root = _fixture(tmp_path)
    summary = analyze_experiment(root)
    with summary.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["mean_pixel_mae"]) == pytest.approx(2)
    folder = root / "bc7_error_analysis" / "example"
    for name in ("pixel_error.png", "block_error.png", "wavelet_residual_energy.png",
                 "pixel_error.npy", "block_error.npy", "edge_mask.npy", "metrics.json"):
        assert (folder / name).exists()
    assert (root / "bc7_error_analysis" / "error_report.md").exists()


def test_missing_decoded_fails(tmp_path):
    root = _fixture(tmp_path)
    (root / "artifacts" / "example_baseline" / "decoded.png").unlink()
    with pytest.raises(FileNotFoundError, match="Missing baseline decoded"):
        analyze_experiment(root)
