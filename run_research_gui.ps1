# Convenience launcher for the GUI once desktop/main.py is implemented.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing project .venv. Run setup_windows.ps1 first." }
$entry = Join-Path $PSScriptRoot "desktop\main.py"
if (-not (Test-Path $entry)) { throw "Desktop GUI has not been implemented yet. Run the CLI or wait for the GUI milestone." }
& $python $entry
exit $LASTEXITCODE
