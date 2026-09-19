$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw 'Docker CLI was not found. Install Docker Desktop and open a new PowerShell window.'
}
$dockerExecutable = $dockerCommand.Source
& $dockerExecutable info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop and wait for the engine to be ready.' }
& $dockerExecutable compose up --build -d --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Inspect docker compose logs.' }
$health = Invoke-RestMethod http://localhost:8080/health
if ($health.status -ne 'ok') { throw 'The API is not reachable from Windows.' }
Write-Host 'API: http://localhost:8080/health'
Write-Host 'Local email inbox: http://localhost:8025'
Write-Host 'Demo login: demo@example.com / demo-pass-123'
