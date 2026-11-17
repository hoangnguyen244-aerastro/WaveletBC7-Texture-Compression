import numpy as np
import pytest
from PIL import Image

from src.wavelet_bc7.rgb_policy import extract_rgb
from src.wavelet import wavelet_preprocess
from src.metrics import measure


def test_rgba_alpha_does_not_change_rgb_input_or_wavelet_or_metrics():
    rng = np.random.default_rng(2026)
    rgb = rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
    rgba_a = np.dstack((rgb, np.zeros((16, 16), dtype=np.uint8)))
    rgba_b = np.dstack((rgb, rng.integers(0, 256, size=(16, 16), dtype=np.uint8)))
    a = extract_rgb(Image.fromarray(rgba_a, "RGBA"))
    b = extract_rgb(Image.fromarray(rgba_b, "RGBA"))
    assert np.array_equal(a, rgb)
    assert np.array_equal(b, rgb)
    for mode in ("identity", "fixed", "adaptive"):
        assert np.array_equal(wavelet_preprocess(a, mode=mode, strength=4),
                              wavelet_preprocess(b, mode=mode, strength=4))
    assert measure(a, b)["mae"] == 0


def test_rgb_input_is_preserved():
    rgb = np.full((8, 8, 3), 127, dtype=np.uint8)
    assert np.array_equal(extract_rgb(Image.fromarray(rgb, "RGB")), rgb)


def test_palette_input_is_rejected_instead_of_silent_conversion():
    with pytest.raises(ValueError, match="RGB/RGBA"):
        extract_rgb(Image.new("P", (4, 4)))
