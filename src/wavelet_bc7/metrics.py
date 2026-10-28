"""Full-reference image metrics on uint8 RGB sRGB code values."""

import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def measure(original: np.ndarray, decoded: np.ndarray) -> dict[str, float]:
    a, b = np.asarray(original), np.asarray(decoded)
    if a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError("Both images must have identical HxWx3 shape")
    if a.dtype != np.uint8 or b.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB")
    win_size = min(7, a.shape[0], a.shape[1])
    if win_size % 2 == 0:
        win_size -= 1
    if win_size < 3:
        raise ValueError("SSIM requires images at least 3x3")
    return {
        "psnr_db": float(peak_signal_noise_ratio(a, b, data_range=255)),
        "ssim": float(structural_similarity(a, b, channel_axis=2, data_range=255, win_size=win_size)),
        "mae": float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean()),
    }
