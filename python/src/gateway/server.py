import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId

server = Flask(__name__)

mongo_video = PyMongo(
        server, 
        uri="mongodb://host.minikube.internal:27017/videos"
    )

mongo_mp3 = PyMongo(
        server, 
        uri="mongodb://host.minikube.internal:27017/mp3s"
    )

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

@server.route('/login', methods=['POST'])
def login():
    token, err = access.login(request)
    
    if not err:
        return token
    else:
        message, status = err
        return message, status

@server.route('/upload', methods=['POST'])
def upload():
    print("ENTERED /upload", flush=True)

    access_data, err = validate.token(request)
    print("AFTER validate.token", access_data, err, flush=True)

    if err:
        message, status = err
        return message, status

    access_data = json.loads(access_data)
    print("AFTER json.loads", access_data, flush=True)

    if not access_data.get("admin"):
        return "Not Authorized", 401

    if len(request.files) != 1:
        return "Only one file allowed", 400

    for _, f in request.files.items():
        print("CALLING util.upload()", flush=True)
        message, status = util.upload(f, fs_videos, channel, access_data)
        return message, status


@server.route("/download", methods=['GET'])
def download():
    print("ENTERED /download", flush=True)

    access_data, err = validate.token(request)
    print("AFTER validate.token", access_data, err, flush=True)

    if err:
        message, status = err
        return message, status

    access_data = json.loads(access_data)
    print("AFTER json.loads", access_data, flush=True)

    if not access_data.get("admin"):
        return "Not Authorized", 401
    
    fid_string = request.args.get("fid")
    if not fid_string:
        return "Missing fid..fid is required", 400
    
    # file is found..send it back
    try:
        out = fs_mp3s.get(ObjectId(fid_string))
        return send_file(out, download_name=f'{fid_string}.mp3')
    except Exception as err:
        print("ERROR:", err, flush=True)
        return "Internal Server Error", 500
    
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080) 