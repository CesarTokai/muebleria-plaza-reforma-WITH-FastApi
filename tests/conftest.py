import os
# Marcar entorno de pruebas antes de importar módulos de la app
os.environ.setdefault("ENVIRONMENT", "test")
# variables DB dummy
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_DATABASE", "test_db")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Crear motor SQLite in-memory para pruebas
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

