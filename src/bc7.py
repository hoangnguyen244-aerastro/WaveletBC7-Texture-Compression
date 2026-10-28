
import subprocess
from pathlib import Path


class Texconv:
    def __init__(self, executable="tools/texconv.exe"):
        self.executable = Path(executable).resolve()
        if not self.executable.is_file():
            raise FileNotFoundError(
                f"texconv not found: {self.executable}"
            )

    def _run(self, args):
        command = [str(self.executable), *map(str, args)]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"texconv failed:\n{result.stdout}\n"
                f"{result.stderr}"
            )

    def encode_bc7(self, input_png, output_dds):
        input_png = Path(input_png).resolve()
        output_dds = Path(output_dds).resolve()
        output_dds.parent.mkdir(
            parents=True, exist_ok=True
        )

        # -m 1 means one mip level.
        # -srgb preserves intended sRGB color interpretation
        # for albedo textures.
        self._run([
            "-y", "-f", "BC7_UNORM_SRGB",
            "-m", "1",
            "-o", output_dds.parent,
            input_png,
        ])

        generated = (
            output_dds.parent / (input_png.stem + ".dds")
        )
        if not generated.is_file():
            raise RuntimeError(
                f"DDS output not found: {generated}"
            )
        if generated != output_dds:
            generated.replace(output_dds)

        return output_dds

    def decode_png(self, input_dds, output_png):
        input_dds = Path(input_dds).resolve()
        output_png = Path(output_png).resolve()
        output_png.parent.mkdir(
            parents=True, exist_ok=True
        )

        self._run([
            "-y", "-ft", "png",
            "-o", output_png.parent,
            input_dds,
        ])

        generated = (
            output_png.parent / (input_dds.stem + ".png")
        )
        if not generated.is_file():
            raise RuntimeError(
                f"Decoded PNG not found: {generated}"
            )
        if generated != output_png:
            generated.replace(output_png)

        return output_png
