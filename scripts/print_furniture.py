import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import database
from app import models
from sqlalchemy import select

db = database.SessionLocal()
try:
    rows = db.query(models.Furniture).order_by(models.Furniture.id.desc()).limit(10).all()
    print('Furniture rows (last 10):')
    for r in rows:
        print('id=', r.id, ' name=', repr(r.name), ' category_id=', r.category_id, ' category_name=', repr(getattr(r, 'category_name', None)), ' created_at=', r.created_at)
finally:
    db.close()

