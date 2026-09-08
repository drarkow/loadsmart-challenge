$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment..."
python -m venv .venv

Write-Host "Activating virtual environment..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Creating dbt profile..."
New-Item -ItemType Directory -Force -Path "$HOME\.dbt" | Out-Null
Copy-Item ".\dbt_loadsmart\profiles.yml.example" "$HOME\.dbt\profiles.yml" -Force

Write-Host "Copying seed data..."
Copy-Item ".\data\raw\loads.csv" ".\dbt_loadsmart\seeds\raw_loads.csv" -Force

Write-Host "Environment ready. Next:"
Write-Host "  cd dbt_loadsmart"
Write-Host "  dbt debug"
Write-Host "  dbt build"
Write-Host "  dbt docs generate"
