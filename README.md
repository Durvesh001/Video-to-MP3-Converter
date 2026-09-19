# Video to MP3 Converter

A local, containerized Python microservice demo: authenticate, upload a video,
convert its audio asynchronously, receive a local email, and download the MP3.
This is an API project; it does not include a browser upload frontend.

## Start on Windows

1. Start **Docker Desktop** with Linux containers.
2. Open PowerShell in this repository and run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
   ```

The first run downloads images and builds all four services. No host Python,
Minikube, host databases, old virtual environments, or Gmail account are needed.
The Compose project is named `video-to-mp3` and uses its own database volumes.

| Service | Address / credentials |
| --- | --- |
| API health | http://localhost:8080/health |
| Local email inbox (Mailpit) | http://localhost:8025 |
| RabbitMQ management | http://localhost:15672 — `converter` / `local-rabbit-password` |
| Application login | `demo@example.com` / `demo-pass-123` |

All exposed ports bind to localhost. Compose credentials are intentionally
local demo values; this setup is not a production deployment. MySQL and MongoDB
are accessible only inside the Compose network. Mailpit captures emails locally
and does not deliver them to real recipients.

## Run the complete test

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

This checks API health, incorrect and missing credentials, malformed tokens,
invalid/missing download IDs, a real video upload, conversion, a matching local
email, and the downloaded audio using FFprobe. It writes `artifacts/converted.mp3`.
It runs Python inside the gateway container, so Windows Python is unnecessary.

## Convert your own video

```powershell
$token = curl.exe --fail-with-body -sS -X POST http://localhost:8080/login `
    -u "demo@example.com:demo-pass-123"

curl.exe --fail-with-body -X POST http://localhost:8080/upload `
    -H "Authorization: Bearer $token" `
    -F "file=@C:/path/to/your-video.mp4"
```

Uploads accept one video per request, up to 100 MiB including request overhead.
The upload response includes its `video_fid`. Open http://localhost:8025, find
the corresponding email by its Video ID, and copy its **File ID** (the MP3 ID).

```powershell
$mp3Id = "PASTE_MP3_FILE_ID_HERE"
curl.exe --fail-with-body "http://localhost:8080/download?fid=$mp3Id" `
    -H "Authorization: Bearer $token" --output converted.mp3
```

Tokens expire after one day; log in again when needed. A video must contain an
audio track. Invalid conversion jobs are rejected and logged without repeatedly
crashing the worker. Jobs and email failures currently have no automatic retry
or dead-letter storage; inspect logs and upload again after fixing the cause.

## Logs and stopping

Open PowerShell in the project folder and use:

```powershell
docker compose ps
docker compose logs --tail 100 converter notification
docker compose stop
docker compose start
```

`stop` preserves uploaded videos, converted audio, users, and queues. Starting
Docker Desktop is required after reboot. Run `scripts/start.ps1` after code
changes to rebuild. Avoid `docker compose down -v` unless you deliberately want
to erase this project's database and queue data.

Port conflicts on 8080, 8025, or 15672 require changing the corresponding host
port in `compose.yaml`. Existing Kubernetes manifests remain a separate legacy
deployment path; they are not used or validated by this local Compose setup.
Existing databases with plaintext passwords require password migration before
using the updated auth service. The new local database seeds a hashed demo
password only when `DEMO_USER_PASSWORD` is configured, and never overwrites an
existing account.

## Service flow

`Client -> gateway -> auth / MySQL`

`Upload -> MongoDB GridFS -> RabbitMQ video -> converter -> MP3 GridFS`

`converter -> RabbitMQ mp3 -> notification -> Mailpit`

`Download + JWT + MP3 ID -> gateway -> MP3 GridFS`

Compose waits for database and broker health before starting dependent services.
See [Compose startup ordering](https://docs.docker.com/compose/how-tos/startup-order/).
