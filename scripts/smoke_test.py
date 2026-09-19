"""Exercise the local API, conversion, email capture, and downloaded MP3.

Run with Python 3, or inside the gateway container (see README).
"""
import argparse
import base64
import json
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8080")
    parser.add_argument("--mail", default="http://localhost:8025")
    parser.add_argument("--video", default="python/src/converter/test.mp4")
    parser.add_argument("--output", default="artifacts/converted.mp3")
    args = parser.parse_args()

    def call(url, method="GET", data=None, headers=None, expected=200):
        request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        assert status == expected, f"{method} {url}: expected {expected}, got {status}: {body[:300]!r}"
        return body

    call(args.api + "/health")
    call(args.api + "/upload", method="POST", data=b"", expected=401)
    bad = base64.b64encode(b"demo@example.com:wrong-password").decode()
    call(args.api + "/login", method="POST", headers={"Authorization": "Basic " + bad}, expected=401)
    basic = base64.b64encode(b"demo@example.com:demo-pass-123").decode()
    token = call(args.api + "/login", method="POST", headers={"Authorization": "Basic " + basic}).decode()
    headers = {"Authorization": "Bearer " + token}
    call(args.api + "/download?fid=invalid", headers=headers, expected=400)
    call(args.api + "/download?fid=000000000000000000000000", headers=headers, expected=404)
    call(args.api + "/download?fid=invalid", headers={"Authorization": "Bearer"}, expected=401)

    boundary = uuid.uuid4().hex
    video = Path(args.video).read_bytes()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"test.mp4\"\r\n"
            "Content-Type: video/mp4\r\n\r\n").encode() + video + f"\r\n--{boundary}--\r\n".encode()
    result = json.loads(call(args.api + "/upload", method="POST", data=body,
                            headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"}))
    video_fid = result["video_fid"]
    print(f"Login and validation checks passed. Uploaded video {video_fid}", flush=True)

    deadline = time.monotonic() + 120
    mp3_fid = None
    while time.monotonic() < deadline and not mp3_fid:
        messages = json.loads(call(args.mail + "/api/v1/messages"))
        for message in messages.get("messages", []):
            detail = json.loads(call(args.mail + "/api/v1/message/" + message["ID"]))
            content = detail.get("Text", "")
            if "Video ID: " + video_fid in content:
                match = re.search(r"File ID: ([a-f0-9]{24})", content)
                assert match, "Notification did not contain a valid MP3 ID"
                mp3_fid = match.group(1)
                break
        if not mp3_fid:
            time.sleep(2)
    assert mp3_fid, "No matching notification within 120 seconds; check converter and notification logs"
    audio = call(args.api + "/download?fid=" + mp3_fid, headers=headers)
    assert len(audio) > 128, "Downloaded MP3 is empty or too short"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio)
    print(f"PASS: conversion, local email, and download. MP3 {mp3_fid}: {len(audio)} bytes -> {output}")


if __name__ == "__main__":
    main()
