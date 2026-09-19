$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$dockerExecutable = if ($dockerCommand) { $dockerCommand.Source } else {
    Join-Path $env:LOCALAPPDATA 'Programs\Rancher Desktop\resources\resources\win32\bin\docker.exe'
}
if (-not (Test-Path $dockerExecutable)) { throw 'Docker CLI was not found.' }
$env:PATH = (Split-Path $dockerExecutable -Parent) + ';' + $env:PATH
& $dockerExecutable compose cp ./scripts/smoke_test.py gateway:/tmp/smoke_test.py
if ($LASTEXITCODE -ne 0) { throw 'Start the project first with scripts/start.ps1.' }
& $dockerExecutable compose cp ./python/src/converter/test.mp4 gateway:/tmp/test.mp4
if ($LASTEXITCODE -ne 0) { throw 'Could not copy the test video.' }
& $dockerExecutable compose exec -T gateway python /tmp/smoke_test.py --api http://gateway:8080 --mail http://mailpit:8025 --video /tmp/test.mp4 --output /tmp/converted.mp3
if ($LASTEXITCODE -ne 0) { throw 'End-to-end test failed.' }
New-Item -ItemType Directory -Force artifacts | Out-Null
& $dockerExecutable compose cp gateway:/tmp/converted.mp3 ./artifacts/converted.mp3
if ($LASTEXITCODE -ne 0) { throw 'Could not retrieve the converted MP3.' }
& $dockerExecutable compose cp ./artifacts/converted.mp3 converter:/tmp/smoke-output.mp3
if ($LASTEXITCODE -ne 0) { throw 'Could not copy the MP3 for validation.' }
& $dockerExecutable compose exec -T converter ffprobe -v error -show_entries stream=codec_name,duration -of json /tmp/smoke-output.mp3
if ($LASTEXITCODE -ne 0) { throw 'MP3 media validation failed.' }
Write-Host 'Verified output: artifacts/converted.mp3'
