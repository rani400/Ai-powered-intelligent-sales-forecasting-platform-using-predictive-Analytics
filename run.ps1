# SalesGenie AI - developer commands
#
#   .\run.ps1 setup     install dependencies and create .env
#   .\run.ps1 migrate   apply pending database migrations
#   .\run.ps1 test      run the full automated test suite
#   .\run.ps1 api       start the FastAPI backend on :8000
#   .\run.ps1 ui        start the Streamlit frontend on :8501
#   .\run.ps1 demo      run the end-to-end walkthrough against a running backend
#   .\run.ps1 coverage  measure the prospect record coverage
#   .\run.ps1 status    show the migration state
#   .\run.ps1 check     verify everything (tests + migrations + a live API check)
#   .\run.ps1 lint     run ruff lint and format checks
#
# The API and the UI need separate terminals; use .\run.ps1 api in one and .\run.ps1 ui in another.

param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'migrate', 'status', 'test', 'api', 'ui', 'demo', 'coverage', 'check', 'lint')]
    [string]$Command = 'check'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

switch ($Command) {
    'setup' {
        Write-Step 'Installing backend dependencies'
        python -m pip install -r backend\requirements.txt

        if (-not (Test-Path '.env')) {
            Copy-Item '.env.example' '.env'
            Write-Host 'Created .env from .env.example' -ForegroundColor Green
        } else {
            Write-Host '.env already exists - left unchanged' -ForegroundColor Yellow
        }
    }

    'migrate' {
        Write-Step 'Applying database migrations'
        python backend\scripts\migrate.py
    }

    'status' {
        Write-Step 'Migration status'
        python backend\scripts\migrate.py --status
    }

    'test' {
        Write-Step 'Running the test suite'
        python -m pytest
    }

    'api' {
        Write-Step 'Starting the backend on http://127.0.0.1:8000 (docs at /docs)'
        python -m uvicorn app.main:app --reload --app-dir backend
    }

    'ui' {
        Write-Step 'Starting the Streamlit UI on http://127.0.0.1:8501'
        python -m streamlit run frontend\app.py
    }

    'demo' {
        Write-Step 'End-to-end walkthrough'
        python backend\scripts\demo_walkthrough.py --base-url http://127.0.0.1:8000
    }

    'coverage' {
        Write-Step 'Measuring prospect record coverage'
        python backend\scripts\measure_coverage.py --rows 500 --base-url http://127.0.0.1:8000
    }

    'lint' {
        Write-Step 'Ruff lint'
        ruff check .

        Write-Step 'Ruff format check'
        ruff format --check .
    }

    'check' {
        Write-Step '1/4 Tests'
        python -m pytest

        Write-Step '2/4 Migrations'
        python backend\scripts\migrate.py

        Write-Step '3/4 Migration status'
        python backend\scripts\migrate.py --status

        Write-Step '4/4 Live API check'
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 10
            Write-Host "Backend healthy: $($health.service) v$($health.version)" -ForegroundColor Green
        } catch {
            Write-Host 'Backend not running - start it with: .\run.ps1 api' -ForegroundColor Yellow
        }
    }
}
