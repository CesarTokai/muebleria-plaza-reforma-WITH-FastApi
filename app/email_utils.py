import aiosmtplib
from email.message import EmailMessage

async def send_email(subject, to_email, content):
    message = EmailMessage()
    message["From"] = "tucorreo@tu_dominio.com"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(content)

    await aiosmtplib.send(
        message,
        hostname="smtp.tu_dominio.com",
        port=465,
        username="tucorreo@tu_dominio.com",
        password="tu_password",
        use_tls=True
    )
