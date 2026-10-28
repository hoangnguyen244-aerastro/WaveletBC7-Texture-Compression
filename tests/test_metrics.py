import numpy as np
import pytest

from wavelet_bc7.metrics import measure


def test_identical_image():
    image = np.full((4, 5, 3), 128, dtype=np.uint8)
    result = measure(image, image.copy())
    assert result["mae"] == 0
    assert result["ssim"] == pytest.approx(1)
    assert np.isinf(result["psnr_db"])


def test_shape_mismatch():
    with pytest.raises(ValueError):
        measure(np.zeros((8, 8, 3), dtype=np.uint8), np.zeros((7, 8, 3), dtype=np.uint8))
