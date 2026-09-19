import datetime
import os

import jwt
import pymysql
from flask import Flask, request
from werkzeug.security import check_password_hash, generate_password_hash

server = Flask(__name__)


def database():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.environ["MYSQL_USER"], password=os.environ["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DB", "auth"), port=int(os.getenv("MYSQL_PORT", "3306")),
        connect_timeout=10,
    )


def initialize_demo_user():
    """Only seed a local demo account when explicitly configured."""
    password = os.getenv("DEMO_USER_PASSWORD")
    if not password:
        return
    with database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT IGNORE INTO user (email, password_hash) VALUES (%s, %s)",
                (os.getenv("DEMO_USER_EMAIL", "demo@example.com"), generate_password_hash(password)),
            )
        connection.commit()


@server.get("/health")
def health():
    with database() as connection:
        connection.ping()
    return {"status": "ok"}


@server.post("/login")
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return "Missing credentials", 401
    with database() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM user WHERE email=%s", (auth.username,))
            row = cursor.fetchone()
    if not row or not check_password_hash(row[0], auth.password):
        return "Invalid credentials", 401
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {"username": auth.username, "exp": now + datetime.timedelta(days=1),
         "iat": now, "admin": True},
        os.environ["JWT_SECRET"], algorithm="HS256",
    )


@server.post("/validate")
def validate():
    parts = request.headers.get("Authorization", "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return "Expected a Bearer token", 401
    try:
        return jwt.decode(parts[1], os.environ["JWT_SECRET"], algorithms=["HS256"]), 200
    except jwt.InvalidTokenError:
        return "Not Authorized", 403


if __name__ == "__main__":
    initialize_demo_user()
    server.run(host="0.0.0.0", port=5000)
