# WaveletBC7 Windows bootstrap. Run from any directory: powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
[CmdletBinding()]
param([switch]$SkipTests)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
Write-Host "WaveletBC7 setup at $root"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher 'py' was not found. Install Python 3.11 (64-bit) from python.org with the launcher enabled."
}
& py -3.11 -c "import sys,struct; assert sys.version_info[:2] == (3,11) and struct.calcsize('P') == 8, 'Need 64-bit Python 3.11'"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 64-bit not available. Run: py -0p" }
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython -c "import sys; assert sys.version_info[:2] == (3,11)"
    if ($LASTEXITCODE -ne 0) { throw "Existing .venv is not Python 3.11. Rename .venv, then rerun setup." }
} else {
    if (Test-Path (Join-Path $root ".venv")) { throw "Broken .venv exists. Rename it and rerun setup." }
    & py -3.11 -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed creating project virtual environment." }
}
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
& $venvPython -m pip install -r (Join-Path $root "requirements.txt") -r (Join-Path $root "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "Installing project dependencies failed" }
& $venvPython -c "import sys, numpy, PIL, pywt, skimage, PySide6; print('Python:', sys.executable); print('PySide6:', PySide6.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Dependency verification failed" }
if (-not $SkipTests) {
    & $venvPython -m pytest tests/test_research.py -q
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }
}
$texconv = Join-Path $root "tools\texconv.exe"
if (Test-Path $texconv) { Write-Host "texconv found: $texconv" }
else { Write-Warning "texconv.exe missing at tools\texconv.exe. Install trusted DirectXTex binary before BC7 experiments." }
Write-Host "Setup complete! Use .\run_research_gui.ps1 or .\.venv\Scripts\python.exe -m scripts.run_research --config configs/pilot.json"
