"""Read-only pixel-level audit of RGB/RGBA texture dataset."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from PIL import Image

def audit(root: Path, output: Path):
    root = root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(root.glob("*.png"))
    rows = []
    for path in files:
        record = {"filename": path.name, "mode": "", "width": "", "height": "",
                  "alpha_min": "", "alpha_max": "", "alpha_nonopaque_pixels": "",
                  "alpha_status": "", "size_status": "", "error": ""}
        try:
            with Image.open(path) as im:
                im.load()
                record.update(mode=im.mode, width=im.width, height=im.height,
                              size_status="ok" if im.size == (1024, 1024) else "invalid")
                if im.mode == "RGBA":
                    alpha = im.getchannel("A")
                    minimum, maximum = alpha.getextrema()
                    histogram = alpha.histogram()
                    nonopaque = sum(histogram[:255])
                    record.update(alpha_min=minimum, alpha_max=maximum,
                                  alpha_nonopaque_pixels=nonopaque,
                                  alpha_status="opaque_rgba" if nonopaque == 0 else "nonopaque_rgba")
                elif im.mode == "RGB":
                    record["alpha_status"] = "no_alpha"
                else:
                    record["alpha_status"] = "unsupported_mode"
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["alpha_status"] = "unreadable"
            record["size_status"] = "unreadable"
        rows.append(record)
    fields = list(rows[0]) if rows else ["filename","mode","width","height","alpha_min","alpha_max","alpha_nonopaque_pixels","alpha_status","size_status","error"]
    with (output / "alpha_audit.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(r["alpha_status"] for r in rows)
    bad_size = [r["filename"] for r in rows if r["size_status"] != "ok"]
    nonopaque = [r["filename"] for r in rows if r["alpha_status"] == "nonopaque_rgba"]
    summary = {"total":len(rows), "alpha_status_counts":dict(counts),
               "nonopaque_alpha_files":nonopaque, "invalid_size_files":bad_size,
               "note":"Read-only: original PNG files were not modified. Opaque RGBA may be converted to RGB without changing RGB channels."}
    (output / "alpha_audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("resources/textures/train/albedo"))
    p.add_argument("--output", type=Path, default=Path("results/audits/dataset120_alpha"))
    args = p.parse_args()
    audit(args.root, args.output)

if __name__ == "__main__":
    main()
