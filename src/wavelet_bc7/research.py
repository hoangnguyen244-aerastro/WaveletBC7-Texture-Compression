"""Reproducible Wavelet–BC7 research runner (no web service required)."""
from __future__ import annotations
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from src.wavelet import wavelet_preprocess
from src.wavelet_bc7.codec import Texconv
from src.metrics import measure

@dataclass(frozen=True)
class Method:
    name: str
    mode: str
    strength: float

@dataclass(frozen=True)
class Configuration:
    dataset_manifest: str
    output_directory: str
    texconv_executable: str = "tools/texconv.exe"
    backend: str = "cpu"
    split: str = "validation"
    methods: tuple[Method, ...] = (
        Method("baseline", "identity", 0.0),
        Method("fixed_4", "fixed", 4.0),
        Method("adaptive_4", "adaptive", 4.0),
    )

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda: f.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()

def load_manifest(path: Path, split: str) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"image_id", "path", "split", "material_group"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Manifest requires columns: {sorted(required)}")
        entries = [row for row in reader if row["split"] == split]
    if not entries:
        raise ValueError(f"No images for split '{split}'")
    ids = [r["image_id"] for r in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate image_id in selected split")
    return entries

def environment() -> dict:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    import PIL, pywt, skimage
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "pillow": PIL.__version__,
        "pywavelets": pywt.__version__, "scikit_image": skimage.__version__,
        "git_commit": commit,
    }

def edge_mae(original: np.ndarray, decoded: np.ndarray) -> float:
    from scipy.ndimage import sobel
    gray = original.astype(np.float64).mean(axis=2)
    magnitude = np.hypot(sobel(gray, axis=0), sobel(gray, axis=1))
    mask = magnitude >= np.percentile(magnitude, 75)
    if not mask.any():
        return float("nan")
    return float(np.abs(original.astype(np.float64) -
                        decoded.astype(np.float64))[mask].mean())

def run(config: Configuration) -> Path:
    if config.backend not in {"cpu", "gpu"}:
        raise ValueError("backend must be cpu or gpu")
    if not config.methods or config.methods[0].mode != "identity":
        raise ValueError("First method must be the identity BC7 baseline")
    if len({m.name for m in config.methods}) != len(config.methods):
        raise ValueError("Method names must be unique")
    manifest = Path(config.dataset_manifest).resolve()
    entries = load_manifest(manifest, config.split)
    output = Path(config.output_directory).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite experiment: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "artifacts").mkdir()
    config_dict = asdict(config)
    (output / "config.json").write_text(json.dumps(config_dict, indent=2), encoding="utf-8")
    env = environment()
    exe = Path(config.texconv_executable).resolve()
    if not exe.is_file():
        raise FileNotFoundError(exe)
    env["texconv_path"] = str(exe)
    env["texconv_sha256"] = sha256(exe)
    (output / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    codec = Texconv(str(exe), backend=config.backend)
    rows = []
    for entry in entries:
        image_path = (manifest.parent / entry["path"]).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        with Image.open(image_path) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        image_hash = sha256(image_path)
        for method in config.methods:
            stem = f"{entry['image_id']}_{method.name}"
            folder = output / "artifacts" / stem
            folder.mkdir()
            start = time.perf_counter()
            preprocessed = wavelet_preprocess(rgb, mode=method.mode, strength=method.strength)
            preprocess_ms = (time.perf_counter() - start) * 1000
            pre_png, dds, decoded_png = (folder / "preprocessed.png",
                                         folder / "compressed.dds",
                                         folder / "decoded.png")
            Image.fromarray(preprocessed, "RGB").save(pre_png)
            start = time.perf_counter()
            codec.encode(pre_png, dds)
            encode_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            codec.decode(dds, decoded_png)
            decode_ms = (time.perf_counter() - start) * 1000
            with Image.open(decoded_png) as img:
                decoded = np.asarray(img.convert("RGB"), dtype=np.uint8)
            scores = measure(rgb, decoded)
            rows.append({
                "image_id": entry["image_id"], "material_group": entry["material_group"],
                "split": config.split, "source_sha256": image_hash,
                "width": rgb.shape[1], "height": rgb.shape[0],
                "method": method.name, "mode": method.mode, "strength": method.strength,
                **scores, "edge_mae": edge_mae(rgb, decoded),
                "preprocessing_ms": preprocess_ms, "encode_ms": encode_ms,
                "decode_ms": decode_ms, "dds_bytes": dds.stat().st_size,
                "dds_sha256": sha256(dds),
            })
    path = output / "raw_results.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
