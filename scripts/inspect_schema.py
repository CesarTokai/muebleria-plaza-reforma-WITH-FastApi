import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
import mysql.connector

print('DB:', settings.MYSQL_DATABASE)

conn = mysql.connector.connect(
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    port=int(settings.MYSQL_PORT),
    database=settings.MYSQL_DATABASE
)
cur = conn.cursor()

for table in ('furniture','categories'):
    print('\nTable:', table)
    cur.execute("SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (settings.MYSQL_DATABASE, table))
    rows = cur.fetchall()
    if not rows:
        print('  (no existe)')
    else:
        for r in rows:
            print(' ', r)

cur.close()
conn.close()

