import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
import mysql.connector
from mysql.connector import errorcode

conn = mysql.connector.connect(
    host=settings.MYSQL_HOST,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    port=int(settings.MYSQL_PORT),
    database=settings.MYSQL_DATABASE
)
cur = conn.cursor()

print('Creating backups of furniture and categories...')
try:
    cur.execute('DROP TABLE IF EXISTS furniture_backup')
    cur.execute('CREATE TABLE furniture_backup AS SELECT * FROM furniture')
    cur.execute('DROP TABLE IF EXISTS categories_backup')
    cur.execute('CREATE TABLE categories_backup AS SELECT * FROM categories')
    conn.commit()
    print('Backups created.')
except Exception as e:
    print('Warning: could not create backups (maybe tables missing):', e)
    conn.rollback()

# 1) Add icon_base64 to categories if not exists
print('\n1) Ensure categories.icon_base64 exists')
cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='categories' AND COLUMN_NAME='icon_base64'", (settings.MYSQL_DATABASE,))
if cur.fetchone() is None:
    cur.execute("ALTER TABLE categories ADD COLUMN icon_base64 LONGTEXT NULL")
    conn.commit()
    print('Added categories.icon_base64')
else:
    print('categories.icon_base64 already exists')

# 2) Insert missing categories from furniture.category values
print('\n2) Insert missing categories from furniture.category values')
cur.execute("SELECT DISTINCT `category` FROM furniture WHERE `category` IS NOT NULL AND `category` != ''")
rows = cur.fetchall()
if rows:
    for (cat_name,) in rows:
        # skip if already exists
        cur.execute("SELECT id FROM categories WHERE name=%s", (cat_name,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO categories (name, description) VALUES (%s, %s)", (cat_name, None))
            print(f"Inserted category: {cat_name}")
    conn.commit()
else:
    print('No furniture.category values found')

# 3) Add category_id column if not exists
print('\n3) Ensure furniture.category_id exists')
cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='furniture' AND COLUMN_NAME='category_id'", (settings.MYSQL_DATABASE,))
if cur.fetchone() is None:
    cur.execute("ALTER TABLE furniture ADD COLUMN category_id INT NULL")
    conn.commit()
    print('Added furniture.category_id (NULL)')
else:
    print('furniture.category_id already exists')

# 4) Populate furniture.category_id using categories.name
print('\n4) Populate furniture.category_id from categories.name')
cur.execute("UPDATE furniture f JOIN categories c ON f.category = c.name SET f.category_id = c.id WHERE f.category IS NOT NULL AND f.category != ''")
conn.commit()
print('Updated furniture.category_id for matching names')

# 5) Ensure no NULL category_id remains; if some furniture rows have NULL, set to first category or leave as NULL
cur.execute("SELECT COUNT(*) FROM furniture WHERE category_id IS NULL OR category_id = 0")
null_count = cur.fetchone()[0]
print('Rows with NULL category_id:', null_count)
if null_count > 0:
    # If there is a category named 'uncategorized' use it, else create it
    cur.execute("SELECT id FROM categories WHERE name='uncategorized'")
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO categories (name, description) VALUES ('uncategorized', 'Categoría generada automáticamente')")
        conn.commit()
        cur.execute("SELECT id FROM categories WHERE name='uncategorized'")
        row = cur.fetchone()
    uncategorized_id = row[0]
    cur.execute("UPDATE furniture SET category_id=%s WHERE category_id IS NULL OR category_id = 0", (uncategorized_id,))
    conn.commit()
    print('Assigned uncategorized_id to remaining rows')

# 6) Alter furniture.category_id to NOT NULL and add FK constraint
print('\n6) Add NOT NULL and FK constraint on furniture.category_id')
try:
    cur.execute("ALTER TABLE furniture MODIFY COLUMN category_id INT NOT NULL")
    conn.commit()
    print('Set furniture.category_id NOT NULL')
except Exception as e:
    print('Could not set NOT NULL (maybe already non-null):', e)
    conn.rollback()

# Add foreign key if not exists
cur.execute("SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s AND TABLE_NAME='furniture' AND COLUMN_NAME='category_id' AND REFERENCED_TABLE_NAME='categories'", (settings.MYSQL_DATABASE,))
if cur.fetchone() is None:
    try:
        cur.execute("ALTER TABLE furniture ADD CONSTRAINT fk_furniture_category FOREIGN KEY (category_id) REFERENCES categories(id)")
        conn.commit()
        print('Added foreign key fk_furniture_category')
    except Exception as e:
        print('Could not add foreign key:', e)
        conn.rollback()
else:
    print('Foreign key already exists')

# 7) Optionally add unique index uix_name_category
print('\n7) Ensure unique index uix_name_category (name, category_id)')
cur.execute("SHOW INDEX FROM furniture WHERE Key_name='uix_name_category'")
if cur.fetchone() is None:
    try:
        cur.execute("ALTER TABLE furniture ADD UNIQUE INDEX uix_name_category (name(255), category_id)")
        conn.commit()
        print('Added unique index uix_name_category')
    except Exception as e:
        print('Could not add unique index (maybe duplicate existing names by category):', e)
        conn.rollback()
else:
    print('Unique index already exists')

# 8) Optionally drop furniture.category column
print('\n8) Optionally drop furniture.category column (kept as backup in furniture_backup).')
# We will not drop automatically; user can drop later if desired.

cur.close()
conn.close()
print('\nMigration script finished.')

