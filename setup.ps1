$ErrorActionPreference = 'Stop'

# -----------------------------------------------------------------------------
# Loadsmart Analytics Engineer Challenge - Windows setup
# -----------------------------------------------------------------------------
# This script is intentionally portable:
# - It never hard-codes the repository's absolute path.
# - The dbt DuckDB profile uses a repo-relative path (../data/loadsmart.duckdb)
#   because dbt is run from the dbt_loadsmart directory, as documented in README.
# - It prepares the environment but does NOT run dbt build automatically.
# - Power BI connects directly to data/loadsmart.duckdb; Power BI's table-load
#   parallelism should be disabled to avoid concurrent DuckDB ODBC locks.
# -----------------------------------------------------------------------------

$repoRoot = (Split-Path -Parent $MyInvocation.MyCommand.Path) | Resolve-Path
$repoRoot = $repoRoot.Path
$dbtDir = Join-Path $repoRoot 'dbt_loadsmart'
$dataDir = Join-Path $repoRoot 'data'
$rawData = Join-Path $dataDir 'raw\loads.csv'
$seedDir = Join-Path $dbtDir 'seeds'
$seedFile = Join-Path $seedDir 'raw_loads.csv'
$venvDir = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$venvPip = Join-Path $venvDir 'Scripts\pip.exe'
$requirements = Join-Path $repoRoot 'requirements.txt'
$profilesDir = Join-Path $env:USERPROFILE '.dbt'
$profilesPath = Join-Path $profilesDir 'profiles.yml'

Write-Host ''
Write-Host 'Loadsmart Analytics Engineer Challenge setup' -ForegroundColor Cyan
Write-Host "Repository: $repoRoot"
Write-Host ''

# -----------------------------------------------------------------------------
# Validate repository layout before modifying anything.
# -----------------------------------------------------------------------------
foreach ($requiredPath in @(
    $requirements,
    $dbtDir,
    (Join-Path $dbtDir 'dbt_project.yml'),
    $rawData
)) {
    if (-not (Test-Path $requiredPath)) {
        throw "Required path not found: $requiredPath"
    }
}

# Ensure expected directories exist.
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path $seedDir | Out-Null
New-Item -ItemType Directory -Force -Path $profilesDir | Out-Null

# -----------------------------------------------------------------------------
# Create/reuse Python virtual environment.
# -----------------------------------------------------------------------------
if (-not (Test-Path $venvPython)) {
    Write-Host 'Creating virtual environment...'
    & py -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to create the Python virtual environment.'
    }
} else {
    Write-Host 'Virtual environment already exists; reusing it.'
}

# Upgrade pip without relying on an activated shell.
Write-Host 'Upgrading pip...'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to upgrade pip.'
}

# -----------------------------------------------------------------------------
# Install pinned dependencies.
# -----------------------------------------------------------------------------
Write-Host 'Installing pinned dependencies...'
& $venvPython -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw 'Dependency installation failed.'
}

Write-Host 'Checking dependency consistency...'
& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    throw 'Dependency consistency check failed.'
}

# -----------------------------------------------------------------------------
# Create portable dbt profile.
# IMPORTANT: dbt commands in README run from dbt_loadsmart, so ../data resolves
# to <repo-root>/data regardless of where the repository was cloned.
# -----------------------------------------------------------------------------
Write-Host 'Creating dbt profile...'

$profilesContent = @'
loadsmart_analytics:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../data/loadsmart.duckdb
      threads: 4
'@

Set-Content -Path $profilesPath -Value $profilesContent -Encoding UTF8

Write-Host "dbt profile: $profilesPath"
Write-Host 'DuckDB path in profile: ../data/loadsmart.duckdb'

# -----------------------------------------------------------------------------
# Copy the supplied CSV into the dbt seed directory.
# -----------------------------------------------------------------------------
Write-Host 'Copying seed data...'
Copy-Item -Path $rawData -Destination $seedFile -Force

# -----------------------------------------------------------------------------
# Verify the dbt adapter and MCP SDK without running dbt.
# -----------------------------------------------------------------------------
Write-Host 'Checking dbt DuckDB adapter...'
& $venvPython -c "import dbt.adapters.duckdb; print('dbt-duckdb adapter: OK')"
if ($LASTEXITCODE -ne 0) {
    throw 'dbt-duckdb adapter verification failed.'
}

Write-Host 'Checking MCP SDK...'
& $venvPython -c "from importlib.metadata import version; print('MCP SDK:', version('mcp'))"
if ($LASTEXITCODE -ne 0) {
    throw 'MCP SDK verification failed.'
}

# -----------------------------------------------------------------------------
# Final instructions.
# -----------------------------------------------------------------------------
Write-Host ''
Write-Host 'Environment ready.' -ForegroundColor Green
Write-Host ''
Write-Host 'Next steps:' -ForegroundColor Cyan
Write-Host '  .\.venv\Scripts\Activate.ps1'
Write-Host '  cd dbt_loadsmart'
Write-Host '  dbt debug'
Write-Host '  dbt seed'
Write-Host '  dbt build'
Write-Host '  dbt docs generate'
Write-Host '  cd ..'
Write-Host ''
Write-Host 'The setup script does not start MCP, Jupyter, or Power BI.'
