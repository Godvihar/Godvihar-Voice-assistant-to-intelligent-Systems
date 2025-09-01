import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

__all__ = ['send_email']

# Map names to emails if you want convenience instead of typing emails
EMAIL_CONTACTS = {
    "harshit": "ssit82532@gmail.com",
    "vihar": os.getenv("EMAIL_USER"),
}

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")

def send_email(to_name: str, subject: str, content: str) -> bool:
    to_email = EMAIL_CONTACTS.get(to_name.lower())
    
    if not to_email:
        # If email not found in contacts, prompt for manual input
        print(f"[INFO] No saved email found for {to_name}. Please enter the email address:")
        to_email = input("Email address: ").strip()
        if not to_email or '@' not in to_email:
            print("[ERROR] Invalid email address format.")
            return False

    msg = EmailMessage()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(content)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        print(f"[INFO] Email sent to {to_name} ({to_email})")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Authentication failed. Please check your email credentials.")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERROR] SMTP error occurred: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
