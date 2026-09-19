$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCommand) {
    $dockerExecutable = $dockerCommand.Source
} else {
    $dockerExecutable = Join-Path $env:LOCALAPPDATA 'Programs\Rancher Desktop\resources\resources\win32\bin\docker.exe'
}
if (-not (Test-Path $dockerExecutable)) {
    throw 'Install Rancher Desktop (Moby engine) or Docker Desktop, then run this script again.'
}
$env:PATH = (Split-Path $dockerExecutable -Parent) + ';' + $env:PATH
# The legacy override is safe only with Rancher's unprivileged Windows forwarder.
if ((Test-Path .env) -and ((Get-Content .env -Raw) -match 'compose.rancher-legacy.yaml')) {
    $rdctl = Join-Path (Split-Path $dockerExecutable -Parent) 'rdctl.exe'
    if (-not (Test-Path $rdctl)) { throw 'Remove the legacy COMPOSE_FILE line from .env when switching away from Rancher Desktop.' }
    $settings = (& $rdctl list-settings | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $settings.application.adminAccess -ne $false -or
        $settings.experimental.virtualMachine.networkingTunnel -ne $true) {
        throw 'Legacy networking override requires per-user Rancher Desktop without adminAccess and with its networking tunnel enabled.'
    }
}
& $dockerExecutable info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Start Rancher Desktop or Docker Desktop and wait for the engine to be ready.' }
& $dockerExecutable compose up --build -d --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Inspect docker compose logs.' }
$health = Invoke-RestMethod http://localhost:8080/health
if ($health.status -ne 'ok') { throw 'The API is not reachable from Windows.' }
Write-Host 'API: http://localhost:8080/health'
Write-Host 'Local email inbox: http://localhost:8025'
Write-Host 'Demo login: demo@example.com / demo-pass-123'
