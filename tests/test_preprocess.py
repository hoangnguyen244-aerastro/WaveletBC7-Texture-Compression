import numpy as np
import pytest

from wavelet_bc7.preprocess import wavelet_preprocess


@pytest.mark.parametrize("shape", [(8, 8, 3), (9, 11, 3), (2, 3, 3)])
@pytest.mark.parametrize("mode", ["identity", "fixed", "adaptive"])
def test_preserves_shape_dtype(shape, mode):
    rgb = np.random.default_rng(42).integers(0, 256, size=shape, dtype=np.uint8)
    out = wavelet_preprocess(rgb, mode=mode, strength=4)
    assert out.shape == rgb.shape
    assert out.dtype == np.uint8
    if mode == "identity":
        np.testing.assert_array_equal(out, rgb)


@pytest.mark.parametrize("strength", [-1, float("nan"), float("inf")])
def test_invalid_strength(strength):
    with pytest.raises(ValueError):
        wavelet_preprocess(np.zeros((8, 8, 3), dtype=np.uint8), strength=strength)


def test_invalid_mode_even_at_zero_strength():
    with pytest.raises(ValueError):
        wavelet_preprocess(np.zeros((8, 8, 3), dtype=np.uint8), mode="typo", strength=0)
