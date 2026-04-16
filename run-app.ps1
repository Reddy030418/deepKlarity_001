$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path (Join-Path $backend ".venv\Scripts\python.exe"))) {
  Write-Host "Creating backend virtual environment..."
  python -m venv (Join-Path $backend ".venv")
}

Write-Host "Installing backend dependencies..."
& (Join-Path $backend ".venv\Scripts\python.exe") -m pip install -r (Join-Path $backend "requirements.txt") | Out-Host

if (-not (Test-Path (Join-Path $backend ".env"))) {
  Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
  Write-Host "Installing frontend dependencies..."
  Push-Location $frontend
  npm install | Out-Host
  Pop-Location
}

if (-not (Test-Path (Join-Path $frontend ".env"))) {
  Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env")
}

Write-Host "Starting backend on http://localhost:8000 ..."
Start-Process powershell -ArgumentList '-NoExit','-Command',"cd '$backend'; .\.venv\Scripts\activate; uvicorn app.main:app --reload"

Write-Host "Starting frontend on http://localhost:5173 ..."
Start-Process powershell -ArgumentList '-NoExit','-Command',"cd '$frontend'; npm run dev"

Write-Host "Done. Backend + Frontend terminals opened."
