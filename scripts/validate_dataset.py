"""Inventory and validate RGB albedo datasets; preserve existing pilot manifest.

Run:
  python -m scripts.validate_dataset --root resources/textures/train/albedo
  python -m scripts.validate_dataset --root resources/textures/train/albedo --provenance datasets/provenance.csv --make-splits

Splits require verified source_group_id metadata to prevent leakage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

CATEGORIES = ("brick", "fabric", "metal", "organic", "stone", "wood")
FILENAME = re.compile(r"^(Brick|Fabric|Metal|Organic|Stone|Wood)_(\d{2})\.png$", re.IGNORECASE)
PROVENANCE_FIELDS = ("image_id", "source_group_id", "source_url", "license")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_provenance(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not set(PROVENANCE_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError(f"Provenance must include {PROVENANCE_FIELDS}")
        records = {}
        for row in reader:
            key = row["image_id"].strip()
            if not key or key in records:
                raise ValueError(f"Missing or duplicate provenance image_id: {key!r}")
            records[key] = row
        return records


def inspect(root: Path, provenance: dict) -> tuple[list[dict], list[str], list[str]]:
    rows, errors, warnings = [], [], []
    if not root.is_dir():
        raise FileNotFoundError(root)
    paths = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    for path in paths:
        match = FILENAME.fullmatch(path.name)
        if not match:
            warnings.append(f"Unrecognized name: {path.name}")
        category = match.group(1).lower() if match else "unknown"
        image_id = path.stem.lower()
        record = provenance.get(image_id, {})
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                width, height = image.size
                mode = image.mode
                image_format = image.format
                # Force full pixel decode so truncated files are detected.
                image.load()
                arr = np.asarray(image)
            if image_format != "PNG" or mode != "RGB" or arr.dtype != np.uint8:
                errors.append(f"Expected 8-bit RGB PNG: {path.name} (mode={mode}, dtype={arr.dtype})")
            if (width, height) != (1024, 1024):
                errors.append(f"Expected 1024x1024: {path.name} ({width}x{height})")
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            errors.append(f"Cannot decode {path.name}: {exc}")
            width, height, mode = 0, 0, "invalid"
        rows.append({
            "image_id": image_id, "filename": path.name,
            "material_group": category, "path": str(path.resolve()),
            "width": width, "height": height, "mode": mode,
            "sha256": sha256(path),
            "source_group_id": record.get("source_group_id", "").strip(),
            "source_url": record.get("source_url", "").strip(),
            "license": record.get("license", "").strip(),
        })
    duplicates = defaultdict(list)
    for row in rows:
        duplicates[row["sha256"]].append(row["image_id"])
    for image_ids in duplicates.values():
        if len(image_ids) > 1:
            errors.append("Identical file SHA256: " + ", ".join(image_ids))
    expected = {f"{cat}_{i:02d}" for cat in CATEGORIES for i in range(1, 21)}
    found = {row["image_id"] for row in rows}
    missing, extra = expected - found, found - expected
    if missing:
        errors.append(f"Missing expected textures: {', '.join(sorted(missing))}")
    if extra:
        warnings.append(f"Unexpected textures: {', '.join(sorted(extra))}")
    for key in provenance.keys() - found:
        warnings.append(f"Provenance entry without image: {key}")
    for row in rows:
        if not row["source_group_id"] or not row["source_url"] or not row["license"]:
            warnings.append(f"Provenance incomplete: {row['image_id']}")
    return rows, errors, warnings


def split_rows(rows: list[dict], seed: int = 2026) -> dict[str, str]:
    """Assign independent source groups to splits within each material category.

    60/20/20 is a target, not a guarantee if group sizes are uneven.
    """
    if not rows:
        raise ValueError("No images")
    if any(not r["source_group_id"] or not r["source_url"] or
           not r["license"] or r["license"].lower() in {"unknown", "unverified", "verify-before-publication"}
           for r in rows):
        raise ValueError("Cannot split without complete, verified provenance for every image")
    groups = defaultdict(list)
    for row in rows:
        groups[row["source_group_id"]].append(row)
    for key, members in groups.items():
        if len({r["material_group"] for r in members}) != 1:
            raise ValueError(f"Source group spans material categories: {key}")
    by_category = defaultdict(list)
    for key, members in groups.items():
        by_category[members[0]["material_group"]].append((key, members))
    assignment = {}
    for category, material_groups in sorted(by_category.items()):
        if len(material_groups) < 3:
            raise ValueError(f"{category}: at least 3 independent source groups needed for train/validation/test")
        rng = random.Random(f"{seed}:{category}")
        rng.shuffle(material_groups)
        # Allocate groups greedily to reach approximate 60/20/20 counts.
        totals = Counter()
        total_images = sum(len(members) for _, members in material_groups)
        targets = {"train": 0.6 * total_images, "validation": 0.2 * total_images,
                   "test": 0.2 * total_images}
        for index, (_, members) in enumerate(material_groups):
            if index < 3:
                split = ("train", "validation", "test")[index]
            else:
                split = max(targets, key=lambda s: (targets[s] - totals[s]) / targets[s])
            for row in members:
                assignment[row["image_id"]] = split
            totals[split] += len(members)
    return assignment


def export(root: Path, output: Path, provenance_path: Path | None,
           make_splits: bool = False, seed: int = 2026) -> dict:
    provenance = read_provenance(provenance_path)
    rows, errors, warnings = inspect(root, provenance)
    output.mkdir(parents=True, exist_ok=True)
    inventory = output / "inventory.csv"
    fields = ("image_id", "filename", "material_group", "path", "width", "height",
              "mode", "sha256", *PROVENANCE_FIELDS[1:])
    with inventory.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    splits = None
    if make_splits:
        if errors:
            errors.append("Split creation blocked: dataset validation errors")
        else:
            try:
                splits = split_rows(rows, seed)
                # Manifest paths are relative to the manifest location, not CWD.
                manifest = output / "manifest_v2.csv"
                with manifest.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=[
                        "image_id", "path", "split", "material_group", "license",
                        "source", "source_group_id", "sha256"
                    ])
                    writer.writeheader()
                    for row in rows:
                        writer.writerow({
                            "image_id": row["image_id"],
                            "path": __import__("os").path.relpath(row["path"], output.resolve()).replace("\\", "/"),
                            "split": splits[row["image_id"]],
                            "material_group": row["material_group"],
                            "license": row["license"],
                            "source": row["source_url"],
                            "source_group_id": row["source_group_id"],
                            "sha256": row["sha256"],
                        })
            except ValueError as exc:
                errors.append(str(exc))
    summary = {
        "total": len(rows),
        "per_material": dict(sorted(Counter(r["material_group"] for r in rows).items())),
        "errors": errors, "warnings": warnings,
        "splits": dict(Counter(splits.values())) if splits else None,
        "manifest_generated": bool(splits),
        "note": "SHA256 detects exact duplicate files only; visually similar crops and derivatives require source_group_id review.",
    }
    (output / "validation_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("resources/textures/train/albedo"))
    parser.add_argument("--output", type=Path, default=Path("datasets/integration"))
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--make-splits", action="store_true")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    report = export(args.root, args.output, args.provenance, args.make_splits, args.seed)
    print(json.dumps(report, indent=2))
    if report["errors"] or (args.make_splits and not report["manifest_generated"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
