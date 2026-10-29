import numpy as np
import pytest
from src.wavelet_bc7.analysis import bootstrap_ci
from src.wavelet_bc7.research import edge_mae
from src.wavelet import wavelet_preprocess

def test_identity_and_zero_strength_return_original():
    rgb = np.arange(8*8*3, dtype=np.uint8).reshape(8,8,3)
    assert np.array_equal(wavelet_preprocess(rgb, mode="identity"), rgb)
    assert np.array_equal(wavelet_preprocess(rgb, mode="adaptive", strength=0), rgb)

def test_edge_mae_identical_is_zero():
    rgb = np.arange(8*8*3, dtype=np.uint8).reshape(8,8,3)
    assert edge_mae(rgb, rgb) == 0

def test_bootstrap_determinism():
    a = bootstrap_ci([1,2,3,4], samples=100)
    assert a == bootstrap_ci([1,2,3,4], samples=100)
    assert a[0] <= 2.5 <= a[1]
