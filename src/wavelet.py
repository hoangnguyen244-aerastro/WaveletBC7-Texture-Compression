
import numpy as np
import pywt
from scipy.ndimage import gaussian_filter, sobel


def edge_map(rgb: np.ndarray) -> np.ndarray:
    """Return normalized edge strength in [0, 1]."""
    rgb = rgb.astype(np.float32) / 255.0
    gray = (
        0.2126 * rgb[:, :, 0]
        + 0.7152 * rgb[:, :, 1]
        + 0.0722 * rgb[:, :, 2]
    )
    gx = sobel(gray, axis=1)
    gy = sobel(gray, axis=0)
    magnitude = gaussian_filter(
        np.hypot(gx, gy), sigma=2.0
    )
    scale = np.percentile(magnitude, 95)
    if scale < 1e-8:
        return np.zeros_like(magnitude)
    return np.clip(magnitude / scale, 0, 1)


def soft_threshold(coeff, threshold):
    return (
        np.sign(coeff)
        * np.maximum(np.abs(coeff) - threshold, 0)
    )


def wavelet_preprocess(
    rgb: np.ndarray,
    mode: str = "adaptive",
    strength: float = 4.0,
    wavelet: str = "haar",
) -> np.ndarray:
    """
    Input/output: uint8 RGB image, same dimensions.

    mode:
      identity: no preprocessing
      fixed: same threshold everywhere
      adaptive: smaller threshold around strong edges
    """
    if mode == "identity" or strength == 0:
        return rgb.copy()

    if mode not in {"fixed", "adaptive"}:
        raise ValueError(f"Unsupported mode: {mode}")

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected HxWx3 RGB image")

    edges = edge_map(rgb)
    h, w, _ = rgb.shape
    result = np.empty((h, w, 3), dtype=np.float32)

    for channel in range(3):
        plane = rgb[:, :, channel].astype(np.float32)
        ll, (lh, hl, hh) = pywt.dwt2(
            plane, wavelet, mode="symmetric"
        )

        if mode == "adaptive":
            # Pool edge map into wavelet coefficient cells.
            # Resize through a simple 2x2 mean for Haar.
            # General wavelets may produce other shapes.
            from scipy.ndimage import zoom

            factor_y = ll.shape[0] / h
            factor_x = ll.shape[1] / w
            local_edges = zoom(
                edges, (factor_y, factor_x), order=1
            )
            local_edges = local_edges[
                :ll.shape[0], :ll.shape[1]
            ]

            # Handle rounding differences in array shapes.
            padded = np.zeros_like(ll)
            ph = min(padded.shape[0], local_edges.shape[0])
            pw = min(padded.shape[1], local_edges.shape[1])
            padded[:ph, :pw] = local_edges[:ph, :pw]

            threshold = strength * (1 - 0.85 * padded)
        else:
            threshold = strength

        details = tuple(
            soft_threshold(c, threshold)
            for c in (lh, hl, hh)
        )

        reconstructed = pywt.idwt2(
            (ll, details), wavelet, mode="symmetric"
        )
        result[:, :, channel] = reconstructed[:h, :w]

    return np.clip(
        np.rint(result), 0, 255
    ).astype(np.uint8)
