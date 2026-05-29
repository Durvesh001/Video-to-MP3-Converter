import smtplib, os
from email.message import EmailMessage
import json

def notification(message):
    # Implementation of email notification logic
    try:
        message = json.loads(message)
        mp3_fid = message.get("mp3_fid")
        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        receiver_address = message["username"]
        
        msg = EmailMessage()
        msg.set_content(f"Your mp3 file is ready. File ID: {mp3_fid}")
        msg['Subject'] = 'MP3 Download Ready'
        msg['From'] = sender_address
        msg['To'] = receiver_address
        
        session = smtplib.SMTP('smtp.gmail.com', 587)
        
        session.starttls()
        session.login(sender_address, sender_password)
        session.send_message(msg)
        session.quit()
        
        print(f"Email sent to {receiver_address} for mp3_fid: {mp3_fid}", flush=True)
    except Exception as err:
        print(f"Failed to send email: {err}", flush=True)
        return err