import os
# Marcar entorno de pruebas antes de importar módulos de la app
os.environ.setdefault("ENVIRONMENT", "test")
# variables DB dummy (solo usadas si USE_MYSQL_FOR_TESTS=1)
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_DATABASE", "test_db")

# Suprimir advertencias conocidas durante ejecución de tests
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    from sqlalchemy.exc import SAWarning, MovedIn20Warning  # type: ignore
    warnings.filterwarnings("ignore", category=SAWarning)
    warnings.filterwarnings("ignore", category=MovedIn20Warning)
except Exception:
    # si no están disponibles, suprimir SAWarning por nombre
    warnings.filterwarnings("ignore", message=r".*Dialect sqlite.*does \* not \* support Decimal objects.*")
    warnings.filterwarnings("ignore", message=r".*Deprecated API features detected.*")

import sys
from pathlib import Path
# Insertar la raíz del proyecto en sys.path para importar el paquete `app` local
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Elegir motor de tests: MySQL (si USE_MYSQL_FOR_TESTS=1) o SQLite in-memory por defecto
USE_MYSQL = os.environ.get("USE_MYSQL_FOR_TESTS", "0") == "1"

if USE_MYSQL:
    # Construir URL para MySQL usando mysql-connector-python driver
    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    host = os.environ.get("MYSQL_HOST")
    port = os.environ.get("MYSQL_PORT")
    database = os.environ.get("MYSQL_DATABASE")
    mysql_url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(mysql_url)
else:
    # Crear motor SQLite in-memory para pruebas (fallback rápido y sin necesidad de DB externa)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Importar modelos y crear tablas
import importlib
import app.models as models

models.Base.metadata.create_all(bind=engine)

@pytest.fixture()
def db():
    """Fixture que provee una sesión de DB para tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
