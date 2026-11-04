"""Synthetic fixtures test the analysis code, not BC7 quality."""
import csv
import pytest

from scripts.analyze_sweep import MODES, STRENGTHS, summarize


def _write_fixture(path, omit=None):
    fields = ["image_id", "method", "mode", "strength", "psnr_db", "ssim", "mae", "edge_mae"]
    rows = []
    for image in ("brick", "wood"):
        rows.append(dict(image_id=image, method="baseline", mode="identity", strength=0,
                         psnr_db=40, ssim=0.98, mae=2, edge_mae=3))
        for mode in MODES:
            for strength in STRENGTHS:
                key = (image, mode, strength)
                if key == omit:
                    continue
                delta = strength / (2 if mode == "adaptive" else 1)
                rows.append(dict(image_id=image, method=f"{mode}_{strength}", mode=mode,
                                 strength=strength, psnr_db=40-delta, ssim=0.98-delta/100,
                                 mae=2+delta, edge_mae=3+delta))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_sweep_exports_real_paired_metrics(tmp_path):
    raw = tmp_path / "raw_results.csv"
    _write_fixture(raw)
    summary, report = summarize(raw)
    with summary.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    adaptive = next(r for r in rows if r["mode"] == "adaptive" and float(r["strength"]) == 4)
    assert float(adaptive["mean_improvement_psnr_db"]) == pytest.approx(-2)
    assert float(adaptive["mean_improvement_mae"]) == pytest.approx(-2)
    assert float(adaptive["fraction_improved_psnr_db"]) == 0
    assert "exploratory" in report.read_text(encoding="utf-8")
    assert (tmp_path / "figures" / "psnr_strength.png").exists()


def test_sweep_rejects_missing_pair(tmp_path):
    raw = tmp_path / "raw_results.csv"
    _write_fixture(raw, omit=("wood", "fixed", 1.0))
    with pytest.raises(ValueError, match="Incomplete sweep"):
        summarize(raw)


def test_sweep_rejects_duplicate_pair(tmp_path):
    raw = tmp_path / "raw_results.csv"
    _write_fixture(raw)
    with raw.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with raw.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writerow(rows[0])
    with pytest.raises(ValueError, match="Duplicate"):
        summarize(raw)
