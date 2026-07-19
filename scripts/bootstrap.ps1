<#
.SYNOPSIS
    Bootstrap script to initialize Khushi AI developer environment.
.DESCRIPTION
    Creates a python virtual environment, activates it, upgrades pip,
    installs requirements, and runs standard compiling checks.
.EXAMPLE
    .\scripts\bootstrap.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "=== Khushi AI Developer Bootstrapper ===" -ForegroundColor Purple

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+."
    Exit 1
}

# 1. Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "[1/4] Creating virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
} else {
    Write-Host "[1/4] Virtual environment (.venv) already exists. Skipping creation." -ForegroundColor Yellow
}

# 2. Upgrade pip and install requirements
Write-Host "[2/4] Installing Python requirements..." -ForegroundColor Cyan
$PipPath = ".\.venv\Scripts\pip.exe"
if (-not (Test-Path $PipPath)) {
    $PipPath = "python"
    Write-Host "Virtual environment pip not found, using global python..." -ForegroundColor Yellow
}

& $PipPath install --upgrade pip
& $PipPath install -r requirements.txt

# 3. Perform code sanity compilation check
Write-Host "[3/4] Running code compilation check..." -ForegroundColor Cyan
$PythonPath = ".\.venv\Scripts\python.exe"
& $PythonPath -m compileall .

# 4. Verify test suite
Write-Host "[4/4] Verifying test suite integrity..." -ForegroundColor Cyan
$PytestPath = ".\.venv\Scripts\pytest.exe"
if (Test-Path $PytestPath) {
    & $PytestPath --version
    Write-Host "Bootstrap completed successfully! Run '.\.venv\Scripts\pytest' to execute unit tests." -ForegroundColor Green
} else {
    Write-Host "Bootstrap completed, but pytest was not found." -ForegroundColor Yellow
}
