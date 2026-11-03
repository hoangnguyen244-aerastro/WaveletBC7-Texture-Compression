# Launch WaveletBC7 GUI using the project-local Python environment.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing project .venv. Run setup_windows.ps1 first." }
& $python -m desktop.main
exit $LASTEXITCODE
