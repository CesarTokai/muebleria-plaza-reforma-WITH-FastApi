import importlib.util
import sys
from pathlib import Path

proj_root = Path(__file__).resolve().parents[1]
main_path = proj_root / 'app' / 'main.py'

spec = importlib.util.spec_from_file_location('local_main', str(main_path))
module = importlib.util.module_from_spec(spec)
# Ensure project root is on sys.path first so local imports in main.py work
sys.path.insert(0, str(proj_root))
spec.loader.exec_module(module)
app = getattr(module, 'app')

for route in app.routes:
    print(route.path, getattr(route, 'methods', None), getattr(route, 'name', None))

