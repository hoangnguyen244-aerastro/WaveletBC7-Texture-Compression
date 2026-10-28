
import struct

import pytest

from wavelet_bc7.dds import inspect_bc7_dds


def test_valid_bc7_dds(tmp_path):
    width = height = 8
    payload = bytes(4 * 16)

    data = bytearray(148)
    data[:4] = b"DDS "

    struct.pack_into("<I", data, 4, 124)
    struct.pack_into("<I", data, 12, height)
    struct.pack_into("<I", data, 16, width)
    struct.pack_into("<I", data, 28, 1)

    # DDS pixel format
    struct.pack_into("<I", data, 76, 32)
    data[84:88] = b"DX10"

    # DX10 extended header
    struct.pack_into(
        "<5I", data, 128,
        99, 3, 0, 1, 0
    )

    path = tmp_path / "test.dds"
    path.write_bytes(data + payload)

    info = inspect_bc7_dds(path)

    assert info.width == 8
    assert info.height == 8
    assert info.dxgi_format == 99
    assert info.payload_bytes == 64


def test_reject_invalid_dds(tmp_path):
    path = tmp_path / "broken.dds"
    path.write_bytes(b"not a DDS")

    with pytest.raises(ValueError):
        inspect_bc7_dds(path)
