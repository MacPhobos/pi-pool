"""Alembic migration environment configuration.

Reads database connection from config.json to avoid circular dependency with Config.py.
"""

from logging.config import fileConfig
import json
import os
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import Base and models for autogenerate support
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.Base import Base
from src.db.models import DeviceRuntime, SensorReading, Event

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def loadConfigFromJson():
    """Load database configuration from config.json files.

    Reads config.json, then overlays config_custom.json if present.
    Returns dict with dbName, dbUser, dbPassword keys.
    """
    configPath = Path(__file__).parent.parent / 'config.json'
    customConfigPath = Path(__file__).parent.parent / 'config_custom.json'

    # Load default config
    with open(configPath) as f:
        cfg = json.load(f)

    # Overlay custom config if exists
    if customConfigPath.exists():
        with open(customConfigPath) as f:
            customCfg = json.load(f)
            cfg.update(customCfg)

    return {
        'dbName': cfg.get('dbName', 'pipool'),
        'dbUser': cfg.get('dbUser', 'pipool'),
        'dbPassword': cfg.get('dbPassword', 'pipool'),
        'dbHost': cfg.get('dbHost', 'localhost'),
    }


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    dbConfig = loadConfigFromJson()
    url = f"postgresql://{dbConfig['dbUser']}:{dbConfig['dbPassword']}@{dbConfig['dbHost']}/{dbConfig['dbName']}"

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    dbConfig = loadConfigFromJson()
    url = f"postgresql://{dbConfig['dbUser']}:{dbConfig['dbPassword']}@{dbConfig['dbHost']}/{dbConfig['dbName']}"

    # Override sqlalchemy.url in alembic.ini
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
