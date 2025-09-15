from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()  # Carga variables del .env al entorno

class Settings:
    # Base de Datos
    MYSQL_USER: str = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE")

    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clave_secreta_por_defecto_no_usar_en_produccion")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Email
    SMTP_USER: str = os.getenv("SMTP_USER")
    SMTP_PASS: str = os.getenv("SMTP_PASS")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))

    # Aplicación
    APP_NAME: str = os.getenv("APP_NAME", "Mueblería Plaza Reforma")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Validación de base de datos
    def validate_database_settings(self) -> Optional[str]:
        """Valida que todas las configuraciones de base de datos estén presentes"""
        missing = []
        if not self.MYSQL_USER:
            missing.append("MYSQL_USER")
        if not self.MYSQL_PASSWORD:
            missing.append("MYSQL_PASSWORD")
        if not self.MYSQL_HOST:
            missing.append("MYSQL_HOST")
        if not self.MYSQL_PORT:
            missing.append("MYSQL_PORT")
        if not self.MYSQL_DATABASE:
            missing.append("MYSQL_DATABASE")

        if missing:
            return f"Faltan las siguientes variables de entorno: {', '.join(missing)}"
        return None

    # Validación de email
    def validate_email_settings(self) -> Optional[str]:
        """Valida que todas las configuraciones de email estén presentes"""
        missing = []
        if not self.SMTP_USER:
            missing.append("SMTP_USER")
        if not self.SMTP_PASS:
            missing.append("SMTP_PASS")
        if not self.SMTP_SERVER:
            missing.append("SMTP_SERVER")

        if missing:
            return f"Faltan las siguientes variables de entorno para email: {', '.join(missing)}"
        return None

settings = Settings()
