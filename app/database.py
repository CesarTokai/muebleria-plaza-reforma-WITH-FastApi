from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import mysql.connector
from mysql.connector import Error
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Función para crear la base de datos si no existe
def create_database_if_not_exists():
    try:
        # Conexión a MySQL sin especificar base de datos
        connection = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            port=settings.MYSQL_PORT
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Verificar si la base de datos existe
            cursor.execute(f"SHOW DATABASES LIKE '{settings.MYSQL_DATABASE}'")
            result = cursor.fetchone()

            # Si no existe, crearla
            if not result:
                cursor.execute(f"CREATE DATABASE {settings.MYSQL_DATABASE}")
                logger.info(f"Base de datos '{settings.MYSQL_DATABASE}' creada exitosamente.")
            else:
                logger.info(f"La base de datos '{settings.MYSQL_DATABASE}' ya existe.")

            cursor.close()
            connection.close()
            logger.info("Conexión a MySQL cerrada")

    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        raise Exception(f"Error de conexión a MySQL: {e}")

# Crear la base de datos si no existe
try:
    create_database_if_not_exists()
except Exception as e:
    logger.error(f"No se pudo crear la base de datos: {e}")
    # Continuamos de todos modos, ya que podría ser un error temporal

# URL de conexión para SQLAlchemy
SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)

# Crear el motor de SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
