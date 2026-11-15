"""Synthetic dataset tests; no claims about uploaded image contents."""
import csv
import json

import numpy as np
import pytest
from PIL import Image

from scripts.validate_dataset import export, split_rows


def test_grouped_split_prevents_leakage():
    rows = []
    for category in ("brick", "wood"):
        for group in range(5):
            for image in range(2):
                rows.append({
                    "image_id": f"{category}_{group}_{image}",
                    "material_group": category,
                    "source_group_id": f"{category}-source-{group}",
                    "source_url": "https://example.org/source",
                    "license": "CC0",
                })
    assigned = split_rows(rows)
    for category in ("brick", "wood"):
        assert {assigned[r["image_id"]] for r in rows if r["material_group"] == category} == {
            "train", "validation", "test"
        }
    for group in range(5):
        assert assigned[f"brick_{group}_0"] == assigned[f"brick_{group}_1"]


def test_split_rejects_missing_provenance():
    with pytest.raises(ValueError, match="provenance"):
        split_rows([{"image_id": "brick_01", "material_group": "brick",
                     "source_group_id": "", "source_url": "", "license": ""}])


def test_inventory_reports_missing_files_without_mutating_pilot(tmp_path):
    root = tmp_path / "albedo"
    root.mkdir()
    Image.fromarray(np.zeros((1024, 1024, 3), dtype=np.uint8), "RGB").save(root / "Brick_01.png")
    output = tmp_path / "report"
    result = export(root, output, None)
    assert result["total"] == 1
    assert any("Missing expected" in err for err in result["errors"])
    assert (output / "inventory.csv").is_file()
    assert (output / "validation_report.json").is_file()
    assert not (output / "manifest_v2.csv").exists()


def test_rejects_duplicate_file_hash(tmp_path):
    root = tmp_path / "albedo"
    root.mkdir()
    image = Image.fromarray(np.zeros((1024, 1024, 3), dtype=np.uint8), "RGB")
    image.save(root / "Brick_01.png")
    image.save(root / "Brick_02.png")
    result = export(root, tmp_path / "out", None)
    assert any("Identical file SHA256" in err for err in result["errors"])
