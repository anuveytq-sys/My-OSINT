# Run from the repository root in PowerShell.
$ErrorActionPreference = "Stop"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found. Install Python 3.11+ from https://www.python.org/downloads/ and enable Add Python to PATH." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/3] Creating virtual environment..."
    python -m venv .venv
}
$Py = Join-Path (Get-Location) ".venv\Scripts\python.exe"
Write-Host "[2/3] Installing/updating dependencies..."
& $Py -m pip install --upgrade pip
& $Py -m pip install -r requirements.txt
Write-Host "[3/3] Starting My-OSINT Desktop at http://127.0.0.1:5050"
Write-Host "Keep this PowerShell window open. Press Ctrl+C to stop the server."
& $Py webapp.py
