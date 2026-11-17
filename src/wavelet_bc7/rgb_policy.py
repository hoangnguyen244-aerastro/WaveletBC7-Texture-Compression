"""Explicit RGB-only experiment input policy.

The RGB planes are copied exactly from RGB/RGBA/LA? No: only RGB and RGBA
are accepted. Alpha is ignored, never composited, filtered, measured or saved.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def extract_rgb(image: Image.Image) -> np.ndarray:
    """Return uint8 HxWx3 RGB pixels; discard RGBA alpha without compositing.

    RGB(A) images are supported. Reject other modes rather than applying an
    implicit palette, grayscale or color-space conversion. Original files
    are not modified.
    """
    if image.mode not in {"RGB", "RGBA"}:
        raise ValueError(f"RGB-only experiment requires RGB/RGBA input; got {image.mode}")
    image.load()
    array = np.asarray(image, dtype=np.uint8)
    return np.array(array[:, :, :3], dtype=np.uint8, copy=True)
