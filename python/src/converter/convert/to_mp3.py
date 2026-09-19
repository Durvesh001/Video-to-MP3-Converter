import json
import os
import tempfile
from pathlib import Path

import pika
from bson.objectid import ObjectId
from moviepy import VideoFileClip


def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)
    with tempfile.TemporaryDirectory() as directory:
        video_path = Path(directory) / "input.video"
        audio_path = Path(directory) / "output.mp3"
        with fs_videos.get(ObjectId(message["video_fid"])) as source:
            with video_path.open("wb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
        with VideoFileClip(str(video_path)) as video:
            if video.audio is None:
                raise ValueError("The uploaded video has no audio track")
            video.audio.write_audiofile(str(audio_path), logger=None)
        with audio_path.open("rb") as audio:
            fid = fs_mp3s.put(audio, filename=f"{message['video_fid']}.mp3",
                             video_fid=message["video_fid"], username=message["username"])

    message["mp3_fid"] = str(fid)
    try:
        channel.basic_publish(
            exchange="", routing_key=os.getenv("MP3_QUEUE", "mp3"),
            body=json.dumps(message), mandatory=True,
            properties=pika.BasicProperties(delivery_mode=2),
        )
    except Exception:
        fs_mp3s.delete(fid)
        raise
    print(f"Conversion complete: video_fid={message['video_fid']} mp3_fid={fid}", flush=True)
