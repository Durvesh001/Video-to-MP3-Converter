import logging
import os

import pika
from send import email


def main():
    parameters = pika.URLParameters(os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F"))
    parameters.connection_attempts = 10
    parameters.retry_delay = 2
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    queue = os.getenv("MP3_QUEUE", "mp3")
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        try:
            email.notification(body)
        except Exception:
            logging.exception("Notification failed; rejecting job to avoid an endless retry loop")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue, on_message_callback=callback)
    print("Waiting for completed MP3s", flush=True)
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
