# Windows: portable project-local Python environment

## Why the previous installation failed
The command was executed under `C:\Users\Admin` and created `C:\Users\Admin\.venv`, but the project lives on drive D:. A Python virtual environment is intentionally **not portable** between computers and must be recreated after every clone. The repository ignores `.venv/`.

## One-time setup per machine
1. Install **Python 3.11 64-bit** (with Python Launcher `py`) and Git.
2. Clone this branch with GitHub Desktop. Open the project folder in VS Code.
3. In the project folder, right-click `setup_windows.ps1` and choose Run with PowerShell, or execute from PowerShell:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_windows.ps1
   ```
4. The script uses `$PSScriptRoot` so it works from any location, creates `.venv` next to the repository, installs requirements and pytest/PySide6, and runs unit tests.
5. VS Code: Python: Select Interpreter → `.venv\Scripts\python.exe` if not already selected.
6. Put a trusted DirectXTex `texconv.exe` at `tools\texconv.exe`.
7. Run experiment:
   ```powershell
   .\.venv\Scripts\python.exe -m scripts.run_research --config configs/pilot.json
   .\.venv\Scripts\python.exe -m scripts.generate_report results/experiments/pilot_001
   ```
   Change `output_directory` for subsequent runs because a nonempty run directory is not overwritten.

## Troubleshooting
- `py -0p` lists installed Python versions; Python 3.11 64-bit is required.
- Run `Get-Location` to inspect your current directory.
- If `.venv` is corrupted or was copied from another computer, rename or delete **only the project-local `.venv`** and rerun setup; never delete global Python.
- If PowerShell execution policies block direct execution, use the explicit `powershell -NoProfile -ExecutionPolicy Bypass -File ...` command for this trusted repository script.
- `test_gui.py` is only a manual file from an earlier tutorial, not part of the project.
- `run_research_gui.ps1` is only a future launcher: the desktop GUI is not yet implemented.
- Internet is required for initial dependency downloads. For stronger long-term exact reproducibility, introduce a tested hash-locked requirements file and archive the texconv binary SHA-256 and installer.
