import json
import os
import smtplib
from email.message import EmailMessage


def notification(message):
    message = json.loads(message)
    fid = message["mp3_fid"]
    if not fid:
        raise ValueError("A completed MP3 file ID is required")
    sender = os.getenv("SMTP_FROM", os.getenv("GMAIL_ADDRESS", "converter@example.com"))
    username = os.getenv("SMTP_USERNAME", os.getenv("GMAIL_ADDRESS", ""))
    password = os.getenv("SMTP_PASSWORD", os.getenv("GMAIL_PASSWORD", ""))
    msg = EmailMessage()
    msg.set_content(f"Your mp3 file is ready. File ID: {fid}\nVideo ID: {message['video_fid']}")
    msg["Subject"] = "MP3 Download Ready"
    msg["From"], msg["To"] = sender, message["username"]
    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"),
                      int(os.getenv("SMTP_PORT", "587")), timeout=15) as session:
        if os.getenv("SMTP_TLS", "true").lower() == "true":
            session.starttls()
        if username:
            session.login(username, password)
        session.send_message(msg)
    print(f"Notification captured/sent for mp3_fid={fid}", flush=True)
