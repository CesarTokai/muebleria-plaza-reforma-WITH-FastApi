# app/database.py
import os, logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL
import mysql.connector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def env(name, default=None):
    return os.getenv(name, default)

# Lee primero DB_*, si no existen, cae a MYSQL_*
DB_HOST = env("DB_HOST") or env("MYSQL_HOST", "db")
DB_PORT = int(env("DB_PORT") or env("MYSQL_PORT") or "3306")
DB_NAME = env("DB_NAME") or env("MYSQL_DATABASE", "fastapi_auth_db")
DB_USER = env("DB_USER") or env("MYSQL_USER", "root")
DB_PASSWORD = env("DB_PASSWORD") or env("MYSQL_PASSWORD", "")
ENVIRONMENT = env("ENVIRONMENT", "production")
AUTO_CREATE_DB = env("AUTO_CREATE_DB", "0") == "1"

def create_database_if_not_exists():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        if cur.fetchone() is None:
            cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
            logger.info(f"Base de datos '{DB_NAME}' creada.")
        else:
            logger.info(f"La base '{DB_NAME}' ya existe.")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"No se pudo crear la base: {e}")

# Sólo intenta crear DB si lo pides y no estás en tests
if AUTO_CREATE_DB and ENVIRONMENT != "test":
    create_database_if_not_exists()

# Construye URL segura (soporta símbolos en password)
connection_url = URL.create(
    "mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={"charset": "utf8mb4"},
)

engine = create_engine(
    connection_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
