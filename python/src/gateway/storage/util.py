import pika, json

def upload(f, fs, channel, access):
    try:
        fid = fs.put(f)
        print("Uploaded file to gridfs with fid: ", fid, flush=True)
    except Exception as err:
        print("Exception in putting video to gridfs: ", err, flush=True)
        return "Internal Server Error: ", 500
    
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"]
    }
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="rabbitmq",
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        
        channel = connection.channel()
        
        channel.queue_declare(queue="video", durable=True)
        
        channel.basic_publish(
            exchange = "",
            
            # routing_key should match the name of the queue we created in worker.py. It is the rabbitmq queue
            routing_key = "video",
            body = json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,  # Make message persistent and the queue will still exist incase of pod crash and it comes back up 
            ),
        )
        
        connection.close()

    except Exception as err:
        fs.delete(fid)
        print("Exception in publishing message to rabbitmq: ", err, flush=True)
        return "Internal Server Error: ", 500
    return "Upload Successful", 200