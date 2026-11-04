$ErrorActionPreference = 'Stop'

Write-Host '== Python environment =='
if (-not (Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv }
$venvPython = '.\.venv\Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }

Write-Host '== Python syntax =='
& $venvPython -m compileall -q app tests
if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed' }

Write-Host '== Python tests =='
$env:SECRET_KEY = 'local-test-secret-key-change-me-1234567890'
& $venvPython -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }

Write-Host '== Node syntax and tests =='
Push-Location notify
try {
    node --check src/index.js
    if ($LASTEXITCODE -ne 0) { throw 'Node syntax check failed: index.js' }
    node --check src/dispatcher.js
    if ($LASTEXITCODE -ne 0) { throw 'Node syntax check failed: dispatcher.js' }
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
    npm test
    if ($LASTEXITCODE -ne 0) { throw 'Node tests failed' }
} finally {
    Pop-Location
}

Write-Host '== Docker build =='
docker build -t vulntracker:1.0.0 .
if ($LASTEXITCODE -ne 0) { throw 'Docker build failed' }

Write-Host '== Helm validation =='
helm lint helm/vulntracker
if ($LASTEXITCODE -ne 0) { throw 'Helm lint failed' }
helm template vulntracker helm/vulntracker
if ($LASTEXITCODE -ne 0) { throw 'Helm template rendering failed' }

Write-Host 'Validation commands completed. Review each output; this script does not claim production readiness.'
