$ErrorActionPreference = 'Stop'

Write-Host "Setting up Loadsmart Analytics Engineer challenge..."
Write-Host ""

# Prefer Python 3.13 because dbt-duckdb 1.11.0 publishes a Python 3.13
# classifier. dbt-core 1.12.4 supports Python 3.14, but using 3.13 is the
# conservative choice for reproducibility across developer machines.
$pythonCommand = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $availablePython = py -0p 2>$null

    if ($availablePython -match "3\.14") {
        $pythonCommand = "py -3.14"
    }
    elseif ($availablePython -match "3\.13") {
        $pythonCommand = "py -3.13"
    }
}

if (-not $pythonCommand) {
    Write-Error @"
Supported Python version not found.

Please install Python 3.13 or 3.14 and rerun setup.ps1.
"@
    exit 1
}

if (Test-Path '.\.venv') {
    Write-Host "Existing .venv found. Reusing it."
} else {
    Write-Host "Creating virtual environment..."
    if ($pythonCommand -eq "py -3.13") {
        & py -3.13 -m venv .venv
    } else {
        & python -m venv .venv
    }
}

$venvPython = Resolve-Path '.\.venv\Scripts\python.exe'

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

Write-Host "Installing pinned dependencies..."
& $venvPython -m pip install --requirement requirements.txt

Write-Host "Checking dependency consistency..."
& $venvPython -m pip check

Write-Host "Creating dbt profile..."
New-Item -ItemType Directory -Force -Path "$HOME\.dbt" | Out-Null
Copy-Item ".\dbt_loadsmart\profiles.yml.example" "$HOME\.dbt\profiles.yml" -Force

Write-Host "Copying seed data..."
Copy-Item ".\data\raw\loads.csv" ".\dbt_loadsmart\seeds\raw_loads.csv" -Force

Write-Host ""
Write-Host "Environment ready. Next:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  cd dbt_loadsmart"
Write-Host "  dbt debug"
Write-Host "  dbt seed"
Write-Host "  dbt build"
Write-Host "  dbt docs generate"
