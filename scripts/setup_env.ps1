# ==============================================================================
# Environment Setup Script for Gujarat Cyber Crime Social Media Intelligence
# PowerShell Script (Windows)
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Gujarat Cyber Crime Social Media Intelligence & Early Warning   " -ForegroundColor Yellow
Write-Host " Environment Setup & Dependency Installation                    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Check Python installation
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python 3 is not installed or not in system PATH." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Detected Python: $(python --version)" -ForegroundColor Green

# 2. Create Virtual Environment if not present
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[SUCCESS] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "[INFO] Virtual environment already exists." -ForegroundColor Gray
}

# 3. Activate Virtual Environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# 4. Upgrade pip & Install requirements
Write-Host "[INFO] Installing project dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Create .env from template if missing
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Creating local .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[NOTE] Generated .env file. Please review DB credentials before production deployment." -ForegroundColor Magenta
} else {
    Write-Host "[INFO] .env file already present." -ForegroundColor Gray
}

Write-Host "=================================================================" -ForegroundColor Green
Write-Host " Foundation setup complete. Run './scripts/run_dev.ps1' to start!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
