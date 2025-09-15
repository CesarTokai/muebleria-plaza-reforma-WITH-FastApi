from email.message import EmailMessage
import aiosmtplib
from .config import settings
import logging

# Configurar logger
logger = logging.getLogger(__name__)

async def send_email(subject, to_email, content, html_content=None):
    """
    Envía un correo electrónico.

    Args:
        subject (str): Asunto del correo
        to_email (str): Dirección de correo del destinatario
        content (str): Contenido del correo en texto plano
        html_content (str, optional): Contenido del correo en HTML. Por defecto es None.

    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    # Validar configuración de email
    email_validation = settings.validate_email_settings()
    if email_validation:
        logger.error(f"Error en configuración de email: {email_validation}")
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(content)

    # Añadir contenido HTML si está disponible
    if html_content:
        message.add_alternative(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=True
        )
        logger.info(f"Correo enviado a {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando correo a {to_email}: {str(e)}")
        return False

async def send_reset_code_email(to_email, code):
    """
    Envía un correo con código de recuperación de contraseña.

    Args:
        to_email (str): Dirección de correo del destinatario
        code (str): Código de recuperación

    Returns:
        bool: True si el correo se envió correctamente, False en caso contrario
    """
    subject = f"Código de recuperación - {settings.APP_NAME}"
    text_content = f"""
    Hola,

    Has solicitado un código para recuperar tu contraseña en {settings.APP_NAME}.

    Tu código de recuperación es: {code}

    Este código expirará en 15 minutos.

    Si no has solicitado este código, puedes ignorar este correo.

    Saludos,
    El equipo de {settings.APP_NAME}
    """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Recuperación de Contraseña</h2>
        <p>Hola,</p>
        <p>Has solicitado un código para recuperar tu contraseña en <strong>{settings.APP_NAME}</strong>.</p>
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
            <h3 style="margin: 0; color: #333;">Tu código de recuperación es:</h3>
            <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 10px 0;">{code}</p>
        </div>
        <p>Este código expirará en <strong>15 minutos</strong>.</p>
        <p>Si no has solicitado este código, puedes ignorar este correo.</p>
        <p>Saludos,<br>El equipo de {settings.APP_NAME}</p>
    </div>
    """

    return await send_email(subject, to_email, text_content, html_content)
