# file: migrations/env.py

from logging.config import fileConfig

from alembic import context
# ⬇️⬇️⬇️ Импортируем синхронный create_engine ⬇️⬇️⬇️
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from bot.db.models import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Мы не поддерживаем оффлайн-режим
    raise NotImplementedError("Offline mode is not supported")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # ⬇️⬇️⬇️ КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ ⬇️⬇️⬇️
    from bot.config import settings
    db_url = settings.db_url

    # Для Heroku (PostgreSQL) заменяем асинхронный драйвер на синхронный
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    # Для локальной разработки (SQLite) заменяем асинхронный на синхронный
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
        
    config.set_main_option("sqlalchemy.url", db_url)
    
    # Создаем СИНХРОННЫЙ движок
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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