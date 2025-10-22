from pathlib import Path
import sys
proj_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(proj_root))
import importlib
m = importlib.import_module('app.main')
app = getattr(m, 'app')
for route in app.routes:
    print(route.path, getattr(route, 'methods', None), getattr(route, 'name', None))
print('\nFinished')

