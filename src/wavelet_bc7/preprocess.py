"""Validated wavelet preprocessing for RGB textures."""

import numpy as np

from . import __version__  # noqa: F401
from scipy.ndimage import gaussian_filter, sobel
import pywt


def edge_map(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float32) / 255.0
    gray = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    magnitude = gaussian_filter(np.hypot(sobel(gray, axis=1), sobel(gray, axis=0)), sigma=2.0)
    scale = float(np.percentile(magnitude, 95))
    return np.zeros_like(magnitude) if scale < 1e-8 else np.clip(magnitude / scale, 0, 1)


def soft_threshold(coeff: np.ndarray, threshold: float | np.ndarray) -> np.ndarray:
    return np.sign(coeff) * np.maximum(np.abs(coeff) - threshold, 0)


def wavelet_preprocess(
    rgb: np.ndarray, mode: str = "adaptive", strength: float = 4.0, wavelet: str = "haar"
) -> np.ndarray:
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("Expected HxWx3 uint8 RGB image")
    if rgb.shape[0] < 2 or rgb.shape[1] < 2:
        raise ValueError("Image dimensions must be at least 2x2")
    if mode not in {"identity", "fixed", "adaptive"}:
        raise ValueError(f"Unsupported mode: {mode}")
    if not np.isfinite(strength) or strength < 0:
        raise ValueError("strength must be finite and nonnegative")
    pywt.Wavelet(wavelet)  # Validate even when mode is identity.
    if mode == "identity" or strength == 0:
        return rgb.copy()

    edges = edge_map(rgb) if mode == "adaptive" else None
    h, w, _ = rgb.shape
    result = np.empty_like(rgb)
    for channel in range(3):
        ll, details = pywt.dwt2(rgb[..., channel].astype(np.float32), wavelet, mode="symmetric")
        if edges is None:
            threshold = strength
        else:
            # Match coefficient shape exactly, including odd-sized inputs and non-Haar wavelets.
            from scipy.ndimage import map_coordinates
            ys = np.linspace(0, h - 1, ll.shape[0])
            xs = np.linspace(0, w - 1, ll.shape[1])
            yy, xx = np.meshgrid(ys, xs, indexing="ij")
            local_edges = map_coordinates(edges, [yy, xx], order=1, mode="nearest")
            threshold = strength * (1 - 0.85 * local_edges)
        filtered = tuple(soft_threshold(d, threshold) for d in details)
        reconstructed = pywt.idwt2((ll, filtered), wavelet, mode="symmetric")
        result[..., channel] = np.clip(np.rint(reconstructed[:h, :w]), 0, 255).astype(np.uint8)
    return result
