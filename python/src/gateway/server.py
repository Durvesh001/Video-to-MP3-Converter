import json
import os

import gridfs
from bson.objectid import ObjectId
from flask import Flask, request, send_file
from pymongo import MongoClient

from auth import validate
from auth_svc import access
from storage import util

server = Flask(__name__)
server.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
mongo = MongoClient(os.getenv("MONGO_URI", "mongodb://host.minikube.internal:27017"),
                    serverSelectionTimeoutMS=5000)
fs_videos = gridfs.GridFS(mongo.videos)
fs_mp3s = gridfs.GridFS(mongo.mp3s)


@server.get("/health")
def health():
    mongo.admin.command("ping")
    return {"status": "ok"}


@server.post("/login")
def login():
    token, err = access.login(request)
    return err if err else token


@server.post("/upload")
def upload():
    access_data, err = validate.token(request)
    if err:
        return err
    access_data = json.loads(access_data)
    if not access_data.get("admin"):
        return "Not Authorized", 401
    files = [file for _, file in request.files.items(multi=True)]
    if len(files) != 1:
        return "Only one file allowed", 400
    return util.upload(files[0], fs_videos, None, access_data)


@server.get("/download")
def download():
    access_data, err = validate.token(request)
    if err:
        return err
    if not json.loads(access_data).get("admin"):
        return "Not Authorized", 401
    fid = request.args.get("fid", "")
    if not ObjectId.is_valid(fid):
        return "A valid fid is required", 400
    try:
        result = fs_mp3s.get(ObjectId(fid))
        return send_file(result, download_name=f"{fid}.mp3", mimetype="audio/mpeg", as_attachment=True)
    except gridfs.errors.NoFile:
        return "MP3 not found", 404


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
