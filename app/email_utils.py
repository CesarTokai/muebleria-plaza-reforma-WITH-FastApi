import os
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

async def send_email(subject, to_email, content):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(content)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            use_tls=True
        )
        print(f"Correo enviado a {to_email}")
    except Exception as e:
        print(f"Error enviando correo: {e}")
