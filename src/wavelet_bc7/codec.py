
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess


class Texconv:
    def __init__(
        self,
        executable="tools/texconv.exe",
        backend="cpu",
    ):
        self.executable = Path(executable).resolve()
        self.backend = backend

        if not self.executable.is_file():
            raise FileNotFoundError(self.executable)

        if backend not in {"cpu", "gpu"}:
            raise ValueError("backend must be cpu or gpu")

    def _run(self, args):
        command = [str(self.executable), *args]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed: {command}\n"
                f"{result.stdout}\n{result.stderr}"
            )

    def encode(self, source_png, target_dds):
        source_png = Path(source_png).resolve()
        target_dds = Path(target_dds).resolve()
        target_dds.parent.mkdir(
            parents=True, exist_ok=True
        )

        backend_flag = (
            "-nogpu" if self.backend == "cpu"
            else "-gpu"
        )

        with TemporaryDirectory() as tmp:
            args = [
                "-y",
                "-f", "BC7_UNORM_SRGB",
                "-srgb",
                "-m", "1",
                backend_flag,
            ]
            if self.backend == "gpu":
                args.append("0")

            args.extend(["-o", tmp, str(source_png)])
            self._run(args)

            generated = (
                Path(tmp) / f"{source_png.stem}.dds"
            )
            if not generated.exists():
                raise FileNotFoundError(generated)

            shutil.copy2(generated, target_dds)

        return target_dds

    def decode(self, source_dds, target_png):
        source_dds = Path(source_dds).resolve()
        target_png = Path(target_png).resolve()
        target_png.parent.mkdir(
            parents=True, exist_ok=True
        )

        with TemporaryDirectory() as tmp:
            self._run([
                "-y", "-ft", "png",
                "-o", tmp, str(source_dds),
            ])

            generated = (
                Path(tmp) / f"{source_dds.stem}.png"
            )
            if not generated.exists():
                raise FileNotFoundError(generated)

            shutil.copy2(generated, target_png)

        return target_png
