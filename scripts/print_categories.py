import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import database
from app import crud_category

db = database.SessionLocal()
try:
    rows = crud_category.get_all_categories(db)
    print('Categories:')
    for c in rows:
        print(' id=', c.id, ' name=', repr(c.name), ' created_at=', getattr(c, 'created_at', None))
finally:
    db.close()

