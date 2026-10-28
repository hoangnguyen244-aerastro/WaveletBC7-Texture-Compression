
from dataclasses import dataclass
from pathlib import Path
import struct


BC7_FORMATS = {
    98: "BC7_UNORM",
    99: "BC7_UNORM_SRGB",
}


@dataclass(frozen=True)
class DDSInfo:
    width: int
    height: int
    mip_levels: int
    dxgi_format: int
    format_name: str
    payload_bytes: int
    file_bytes: int


def inspect_bc7_dds(path: str | Path) -> DDSInfo:
    path = Path(path)
    data = path.read_bytes()

    if len(data) < 148:
        raise ValueError("DDS file too short")

    if data[:4] != b"DDS ":
        raise ValueError("Invalid DDS magic")

    header_size = struct.unpack_from("<I", data, 4)[0]
    if header_size != 124:
        raise ValueError("Invalid DDS header size")

    height = struct.unpack_from("<I", data, 12)[0]
    width = struct.unpack_from("<I", data, 16)[0]
    mip_levels = (
        struct.unpack_from("<I", data, 28)[0] or 1
    )

    # DDS_PIXELFORMAT starts at offset 76.
    # FourCC starts at offset 84.
    fourcc = data[84:88]
    if fourcc != b"DX10":
        raise ValueError("Expected DX10 DDS header")

    dxgi_format, dimension, misc_flag, array_size, misc2 = (
        struct.unpack_from("<5I", data, 128)
    )

    if dxgi_format not in BC7_FORMATS:
        raise ValueError(
            f"Not a BC7 DDS: DXGI={dxgi_format}"
        )

    if dimension != 3 or array_size != 1:
        raise ValueError(
            "MVP supports only one 2D texture"
        )

    if mip_levels != 1:
        raise ValueError(
            "MVP expects exactly one mip level"
        )

    expected_payload = (
        ((width + 3) // 4)
        * ((height + 3) // 4)
        * 16
    )

    actual_payload = len(data) - 148
    if actual_payload != expected_payload:
        raise ValueError(
            f"BC7 payload mismatch: "
            f"expected {expected_payload}, "
            f"got {actual_payload}"
        )

    return DDSInfo(
        width=width,
        height=height,
        mip_levels=mip_levels,
        dxgi_format=dxgi_format,
        format_name=BC7_FORMATS[dxgi_format],
        payload_bytes=actual_payload,
        file_bytes=len(data),
    )
