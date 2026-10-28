from pathlib import Path
import numpy as np
from PIL import Image
import pytest
from wavelet_bc7 import pipeline


def test_pipeline_with_fake_codec(tmp_path, monkeypatch):
    source = tmp_path / "input.png"
    Image.fromarray(np.full((8, 8, 3), 128, dtype=np.uint8)).save(source)

    class FakeCodec:
        def __init__(self, **kwargs):
            pass
        def encode(self, png, dds):
            Path(dds).write_bytes(b"fake")
        def decode(self, dds, png):
            Image.open(source).save(png)

    class FakeDDS:
        width = height = 8
        file_bytes = 4

    monkeypatch.setattr(pipeline, "Texconv", FakeCodec)
    monkeypatch.setattr(pipeline, "inspect_bc7_dds", lambda path: FakeDDS())
    result = pipeline.evaluate(source, tmp_path / "out")
    assert result["ssim"] == pytest.approx(1.0)
    assert result["dds_bytes"] == 4
