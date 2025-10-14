import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import database
from app import crud_furniture, crud_category, schemas
from sqlalchemy.orm import Session

print('Connecting DB...')
db = database.SessionLocal()
try:
    # Asegurar que hay una categoría válida
    cats = crud_category.get_all_categories(db)
    if not cats:
        print('No categories found, creating test category "test-cat"')
        cat = crud_category.create_category(db, schemas.CategoryCreate(name='test-cat', description='created by test'))
        cat_id = cat.id
    else:
        cat_id = cats[0].id
        print('Using category id', cat_id)

    # Construir payload válido
    f = schemas.FurnitureCreate(
        name='Test Mesa',
        description='Creada por test script',
        price=123.45,
        category_id=cat_id,
        img_base64=None,
        stock=1,
    )
    print('Calling create_furniture...')
    obj = crud_furniture.create_furniture(db, f)
    print('Created furniture id:', obj.id)
except Exception as e:
    import traceback
    print('Exception during create:')
    traceback.print_exc()
finally:
    db.close()

