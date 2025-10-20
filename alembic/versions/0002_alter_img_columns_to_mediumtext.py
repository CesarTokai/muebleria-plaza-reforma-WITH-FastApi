"""
Alter img_base64 columns to MEDIUMTEXT to avoid 'Data too long' on MySQL when storing base64 images.

Revision ID: 0002_alter_img_columns_to_mediumtext
Revises: 0001_create_categories_and_migrate
Create Date: 2025-10-17 18:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0002_alter_img_columns_to_mediumtext'
down_revision = '0001_create_categories_and_migrate'
branch_labels = None
depends_on = None


def upgrade():
    # Convertir columnas que almacenan base64 (posible long > TEXT) a MEDIUMTEXT en MySQL
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    if dialect_name == 'mysql':
        op.alter_column('furniture', 'img_base64', existing_type=sa.Text(), type_=mysql.MEDIUMTEXT(), nullable=True)
        op.alter_column('furniture_images', 'img_base64', existing_type=sa.Text(), type_=mysql.MEDIUMTEXT(), nullable=False)
        # Si tienes icon_base64 en categories y puede ser grande, convertir también
        try:
            op.alter_column('categories', 'icon_base64', existing_type=sa.Text(), type_=mysql.MEDIUMTEXT(), nullable=True)
        except Exception:
            # ignora si la columna no existe o ya es MEDIUMTEXT
            pass
    else:
        # En otros motores no hacemos nada por defecto
        pass


def downgrade():
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    if dialect_name == 'mysql':
        # revertir a TEXT (nota: podría truncar datos si exceden TEXT limit)
        op.alter_column('furniture_images', 'img_base64', existing_type=mysql.MEDIUMTEXT(), type_=sa.Text(), nullable=False)
        op.alter_column('furniture', 'img_base64', existing_type=mysql.MEDIUMTEXT(), type_=sa.Text(), nullable=True)
        try:
            op.alter_column('categories', 'icon_base64', existing_type=mysql.MEDIUMTEXT(), type_=sa.Text(), nullable=True)
        except Exception:
            pass
    else:
        pass

