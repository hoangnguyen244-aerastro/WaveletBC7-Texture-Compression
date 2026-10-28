
import numpy as np
from skimage.metrics import (
    peak_signal_noise_ratio,
    structural_similarity,
)


def measure(original, decoded):
    if original.shape != decoded.shape:
        raise ValueError(
            f"Shape mismatch: {original.shape} "
            f"vs {decoded.shape}"
        )

    a = original.astype(np.uint8)
    b = decoded.astype(np.uint8)

    return {
        "psnr_db": float(
            peak_signal_noise_ratio(
                a, b, data_range=255
            )
        ),
        "ssim": float(
            structural_similarity(
                a, b,
                channel_axis=2,
                data_range=255,
            )
        ),
        "mae": float(
            np.mean(
                np.abs(
                    a.astype(np.float32)
                    - b.astype(np.float32)
                )
            )
        ),
    }
