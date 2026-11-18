"""Unit tests for deterministic V3 split and independent RGB-only data."""
import csv
from pathlib import Path

import numpy as np
from PIL import Image

from scripts.prepare_v3_validation import prepare, GROUPS


def test_split_is_deterministic_and_stratified(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    for material in GROUPS:
        for i in range(1, 21):
            pixels = np.full((1024, 1024, 4), i, dtype=np.uint8)
            pixels[:, :, 3] = 0 if i % 2 else 255
            Image.fromarray(pixels, "RGBA").save(root / f"{material.capitalize()}_{i:02d}.png")
    output = tmp_path / "out"
    prepare(root, output, "brick")
    with (output / "manifest_v3.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 120
    assert len({r["image_id"] for r in rows}) == 120
    for group in GROUPS:
        selected = [r for r in rows if r["material_group"] == group]
        assert sum(r["split"] == "train" for r in selected) == 12
        assert sum(r["split"] == "validation" for r in selected) == 4
        assert sum(r["split"] == "test" for r in selected) == 4
    before = (output / "manifest_v3.csv").read_bytes()
    prepare(root, output, "wood")
    assert (output / "manifest_v3.csv").read_bytes() == before
