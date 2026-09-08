$ErrorActionPreference = "Stop"

Write-Host "Creating Python virtual environment..."
python -m venv .venv

Write-Host "Activating environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing project dependencies..."
pip install -r requirements.txt

Write-Host "Creating dbt profiles directory..."
New-Item -ItemType Directory -Force "$HOME\.dbt" | Out-Null
Copy-Item .\dbt_loadsmart\profiles.yml.example "$HOME\.dbt\profiles.yml" -Force

Write-Host "Copying challenge CSV into dbt seeds..."
Copy-Item .\data\raw\loads.csv .\dbt_loadsmart\seeds\raw_loads.csv -Force

Write-Host "Checking dbt installation..."
dbt --version

Write-Host "Checking project connection..."
Push-Location .\dbt_loadsmart
dbt debug
Pop-Location

Write-Host "Setup complete."
Write-Host "Next: cd dbt_loadsmart; dbt seed; dbt run; dbt test"
