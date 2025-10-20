#!/usr/bin/env python3
"""
Script para aplicar la migración de MEDIUMTEXT directamente en la base de datos.
Ejecuta este script para cambiar las columnas img_base64 de TEXT a MEDIUMTEXT.
"""

from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_mediumtext_migration():
    """Aplica la migración para cambiar columnas img_base64 a MEDIUMTEXT"""

    # Consultas SQL para cambiar las columnas
    alter_queries = [
        "ALTER TABLE `furniture` MODIFY COLUMN `img_base64` MEDIUMTEXT NULL",
        "ALTER TABLE `furniture_images` MODIFY COLUMN `img_base64` MEDIUMTEXT NOT NULL",
        "ALTER TABLE `categories` MODIFY COLUMN `icon_base64` MEDIUMTEXT NULL"
    ]

    try:
        # Usar begin() para transacción automática con commit
        with engine.begin() as connection:
            # Verificar el tipo de base de datos usando SQLAlchemy
            dialect_name = connection.dialect.name
            logger.info(f"Tipo de base de datos detectado: {dialect_name}")

            # Verificar que estamos conectados a MySQL
            result = connection.execute(text("SELECT VERSION()"))
            version = result.scalar()
            logger.info(f"Versión de la base de datos: {version}")

            # Verificar si es MySQL usando el dialecto de SQLAlchemy
            if dialect_name != 'mysql':
                logger.warning(f"⚠️  No estás usando MySQL (detectado: {dialect_name}). Las columnas se mantendrán como TEXT.")
                return

            logger.info("✅ MySQL detectado, procediendo con la migración...")

            # Aplicar cada consulta
            for query in alter_queries:
                try:
                    logger.info(f"Ejecutando: {query}")
                    connection.execute(text(query))
                    logger.info("✅ Ejecutado correctamente")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "doesn't exist" in error_msg or "unknown table" in error_msg or "unknown column" in error_msg:
                        logger.warning(f"⚠️  Tabla/columna no existe, saltando: {query}")
                        logger.warning(f"    Error: {e}")
                    else:
                        logger.error(f"❌ Error ejecutando {query}: {e}")
                        raise

            logger.info("🎉 ¡Migración completada! Las columnas img_base64 ahora son MEDIUMTEXT")

        # Verificar los cambios en una nueva conexión
        with engine.connect() as connection:
            verify_queries = [
                "DESCRIBE furniture",
                "DESCRIBE furniture_images",
                "DESCRIBE categories"
            ]

            for verify_query in verify_queries:
                try:
                    result = connection.execute(text(verify_query))
                    rows = result.fetchall()
                    table_name = verify_query.split()[1]
                    logger.info(f"\n📋 Estructura de {table_name}:")
                    for row in rows:
                        if 'img_base64' in str(row) or 'icon_base64' in str(row):
                            logger.info(f"   {row}")
                except Exception as e:
                    logger.warning(f"No se pudo verificar tabla {table_name}: {e}")

    except Exception as e:
        logger.error(f"❌ Error general: {e}")
        raise

if __name__ == "__main__":
    apply_mediumtext_migration()
