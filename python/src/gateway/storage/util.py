import json
import os
import pika


def upload(file, fs, channel, access):
    fid = None
    connection = None
    try:
        fid = fs.put(file)
        message = {"video_fid": str(fid), "mp3_fid": None, "username": access["username"]}
        connection = pika.BlockingConnection(pika.URLParameters(
            os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")))
        channel = connection.channel()
        queue = os.getenv("VIDEO_QUEUE", "video")
        channel.queue_declare(queue=queue, durable=True)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange="", routing_key=queue, body=json.dumps(message), mandatory=True,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return {"message": "Upload Successful", "video_fid": str(fid)}, 200
    except Exception:
        if fid is not None:
            fs.delete(fid)
        return "Upload failed; please retry", 503
    finally:
        if connection and connection.is_open:
            connection.close()
