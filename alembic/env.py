from __future__ import with_statement

import sys
import os
from logging.config import fileConfig

from alembic import context

# Añadir la ruta base del proyecto al path para importar app
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# import settings y metadata desde la app
try:
    from app.config import settings
    from app.database import SQLALCHEMY_DATABASE_URL, Base
    target_metadata = Base.metadata
except Exception:
    # Fallback: intentar importar models y su Base
    try:
        from app.models import Base as models_Base
        target_metadata = models_Base.metadata
    except Exception:
        target_metadata = None


def run_migrations_offline():
    """Run migrations in "offline" mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = None
    try:
        url = SQLALCHEMY_DATABASE_URL
    except Exception:
        # fallback to settings
        url = getattr(settings, "SQLALCHEMY_DATABASE_URL", None)

    if url is None:
        raise RuntimeError("No se pudo determinar la URL de la base de datos para migraciones (offline).")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in "online" mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    from sqlalchemy import engine_from_config, pool

    config_section = config.get_section(config.config_ini_section)
    # override sqlalchemy.url con la configuracion de la app
    try:
        config_section["sqlalchemy.url"] = SQLALCHEMY_DATABASE_URL
    except Exception:
        # intentar obtenerla desde settings
        val = getattr(settings, "SQLALCHEMY_DATABASE_URL", None)
        if val:
            config_section["sqlalchemy.url"] = val

    connectable = engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

