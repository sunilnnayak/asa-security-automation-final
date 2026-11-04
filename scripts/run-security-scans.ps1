$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path reports | Out-Null

function Invoke-Scanner([string]$Name, [scriptblock]$Command) {
    Write-Host "`n===== $Name =====" -ForegroundColor Cyan
    & $Command
    $code = $LASTEXITCODE
    if ($null -ne $code -and $code -ne 0) {
        Write-Warning "$Name returned exit code $code. Inspect its report: a non-zero result may indicate findings or a scanner/runtime error."
    }
}

Invoke-Scanner 'Bandit SAST' { bandit -r app -f json -o reports/sast.bandit.json }
Invoke-Scanner 'pip-audit Python SCA' { pip-audit -r requirements.txt -f json -o reports/sca.pip-audit.json }
Invoke-Scanner 'npm audit Node SCA' {
    Push-Location notify
    try { npm audit --json | Out-File -Encoding utf8 ../reports/sca.npm-audit.json } finally { Pop-Location }
}
Invoke-Scanner 'Docker build' { docker build -t vulntracker:1.0.0 . }
Invoke-Scanner 'Trivy container scan' { trivy image --format json --output reports/container.trivy.json vulntracker:1.0.0 }
Invoke-Scanner 'Checkov Helm IaC scan' { checkov -d helm/vulntracker -o json --output-file-path reports/iac.checkov.json }

Write-Host "`nReports are in .\reports. Confirm each JSON file exists, is valid JSON, and represents a completed scan before committing it. Do not treat scanner errors as clean results."
