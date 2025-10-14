import sys
from pathlib import Path
# Insertar la raíz del proyecto en sys.path para priorizar el paquete `app` local
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import traceback
from app.config import settings
import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine

print('Settings used:')
print('HOST:', settings.MYSQL_HOST)
print('PORT:', settings.MYSQL_PORT)
print('USER:', settings.MYSQL_USER)
print('DB:', settings.MYSQL_DATABASE)

print('\n-- Testing mysql-connector connection --')
try:
    conn = mysql.connector.connect(
        host=settings.MYSQL_HOST,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        port=int(settings.MYSQL_PORT) if settings.MYSQL_PORT else None,
        database=settings.MYSQL_DATABASE,
        connection_timeout=5,
    )
    print('mysql-connector: connected, server version:', conn.get_server_info())
    conn.close()
except Exception as e:
    print('mysql-connector: FAILED')
    traceback.print_exc()

print('\n-- Testing SQLAlchemy engine.connect() --')
try:
    url = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    engine = create_engine(url, connect_args={"connect_timeout":5})
    with engine.connect() as conn:
        print('SQLAlchemy: connected, dialect:', engine.dialect.name)
except Exception as e:
    print('SQLAlchemy: FAILED')
    traceback.print_exc()
