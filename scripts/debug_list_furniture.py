import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import traceback
from app import crud_furniture, database

print('Creating DB session...')
SessionLocal = database.SessionLocal

try:
    db = SessionLocal()
    try:
        print('Calling get_all_furniture...')
        res = crud_furniture.get_all_furniture(db)
        print('Result:', res)
    finally:
        db.close()
except Exception as e:
    print('ERROR during get_all_furniture:')
    traceback.print_exc()
    raise

