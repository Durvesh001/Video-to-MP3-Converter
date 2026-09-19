import logging
import os

import gridfs
import pika
from pymongo import MongoClient
from convert import to_mp3


def main():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://host.minikube.internal:27017"),
                         serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    fs_videos, fs_mp3s = gridfs.GridFS(client.videos), gridfs.GridFS(client.mp3s)
    parameters = pika.URLParameters(os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F"))
    parameters.heartbeat = 600
    parameters.connection_attempts = 10
    parameters.retry_delay = 2
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    for queue in (os.getenv("VIDEO_QUEUE", "video"), os.getenv("MP3_QUEUE", "mp3")):
        channel.queue_declare(queue=queue, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.confirm_delivery()

    def callback(ch, method, properties, body):
        try:
            to_mp3.start(body, fs_videos, fs_mp3s, ch)
        except Exception:
            logging.exception("Conversion failed; rejecting job to avoid an endless retry loop")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=os.getenv("VIDEO_QUEUE", "video"), on_message_callback=callback)
    print("Waiting for videos", flush=True)
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()
        client.close()


if __name__ == "__main__":
    main()
