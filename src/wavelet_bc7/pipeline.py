"""End-to-end BC7 evaluation, with one original image as reference."""
from dataclasses import dataclass, asdict
from pathlib import Path
from time import perf_counter
import numpy as np
from PIL import Image
from .preprocess import wavelet_preprocess
from .metrics import measure
from .codec import Texconv
from .dds import inspect_bc7_dds


@dataclass
class Result:
    image: str
    mode: str
    strength: float
    wavelet: str
    backend: str
    width: int
    height: int
    psnr_db: float
    ssim: float
    mae: float
    preprocessing_ms: float
    encode_ms: float
    decode_ms: float
    dds_bytes: int


def evaluate(input_png, output_dir, mode="identity", strength=0.0,
             wavelet="haar", backend="cpu", texconv="tools/texconv.exe"):
    source = Path(input_png)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        original = np.asarray(im.convert("RGB"), dtype=np.uint8)
    t = perf_counter()
    processed = wavelet_preprocess(original, mode, strength, wavelet)
    preprocess_ms = (perf_counter() - t) * 1000
    tag = f"{source.stem}_{mode}_{strength:g}"
    pre_png = destination / f"{tag}_preprocessed.png"
    dds = destination / f"{tag}.dds"
    decoded_png = destination / f"{tag}_decoded.png"
    Image.fromarray(processed).save(pre_png)
    codec = Texconv(executable=texconv, backend=backend)
    t = perf_counter()
    codec.encode(pre_png, dds)
    encode_ms = (perf_counter() - t) * 1000
    info = inspect_bc7_dds(dds)
    if (info.width, info.height) != (original.shape[1], original.shape[0]):
        raise ValueError("BC7 DDS dimensions differ from source image")
    t = perf_counter()
    codec.decode(dds, decoded_png)
    decode_ms = (perf_counter() - t) * 1000
    with Image.open(decoded_png) as im:
        decoded = np.asarray(im.convert("RGB"), dtype=np.uint8)
    scores = measure(original, decoded)
    return asdict(Result(
        image=str(source), mode=mode, strength=float(strength),
        wavelet=wavelet, backend=backend,
        width=original.shape[1], height=original.shape[0],
        preprocessing_ms=preprocess_ms, encode_ms=encode_ms,
        decode_ms=decode_ms, dds_bytes=info.file_bytes, **scores))
