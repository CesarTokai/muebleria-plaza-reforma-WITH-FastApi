"""create categories table and migrate furniture.category to category_id

Revision ID: 0001_create_categories_and_migrate
Revises:
Create Date: 2025-10-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_categories_and_migrate'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1) crear tabla categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 2) añadir columna category_id a furniture (nullable por ahora)
    op.add_column('furniture', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_furniture_category', 'furniture', 'categories', ['category_id'], ['id'])

    # 3) copiar categorías existentes a la tabla categories
    # nota: esto usa SQL compatible con MySQL/SQLite; revisa si tu BD requiere ajustes
    op.execute("""
    INSERT INTO categories (name, description, created_at)
    SELECT DISTINCT category, NULL, CURRENT_TIMESTAMP FROM furniture WHERE category IS NOT NULL;
    """)

    # 4) actualizar furniture.category_id haciendo join con categories por nombre
    op.execute("""
    UPDATE furniture
    SET category_id = (
        SELECT id FROM categories WHERE categories.name = furniture.category
    )
    WHERE furniture.category IS NOT NULL;
    """)

    # 5) establecer category_id NOT NULL (si alguna fila no tiene category_id, falla aquí)
    op.alter_column('furniture', 'category_id', nullable=False)

    # 6) eliminar columna antigua `category`
    op.drop_column('furniture', 'category')

    # 7) crear constraint única nombre+category_id
    op.create_unique_constraint('uix_name_category', 'furniture', ['name', 'category_id'])


def downgrade():
    # Revertir: recrear `category` y rellenarlo a partir de categories, luego borrar FK y tabla
    # 1) añadir columna `category` de vuelta
    op.add_column('furniture', sa.Column('category', sa.String(100), nullable=True))

    # 2) rellenar `category` desde categories
    op.execute("""
    UPDATE furniture
    SET category = (
        SELECT name FROM categories WHERE categories.id = furniture.category_id
    )
    WHERE furniture.category_id IS NOT NULL;
    """)

    # 3) eliminar constraint única
    try:
        op.drop_constraint('uix_name_category', 'furniture', type_='unique')
    except Exception:
        pass

    # 4) eliminar FK y columna category_id
    try:
        op.drop_constraint('fk_furniture_category', 'furniture', type_='foreignkey')
    except Exception:
        pass
    op.drop_column('furniture', 'category_id')

    # 5) borrar tabla categories
    op.drop_table('categories')

