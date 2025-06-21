# file: migrations/env.py

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from bot.db.models import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # ⬇️⬇️⬇️ КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ ⬇️⬇️⬇️
    from bot.config import settings

    # Получаем URL из нашего основного конфига
    db_url = settings.db_url
    
    # Для Heroku (PostgreSQL) заменяем асинхронный драйвер на синхронный
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    # Для локальной разработки (SQLite) заменяем асинхронный на синхронный
    elif db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
        
    # Передаем исправленный URL в конфиг Alembic
    config.set_main_option("sqlalchemy.url", db_url)
    
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    # В оффлайн-режиме мы не можем использовать асинхронный код
    # run_migrations_offline()
    raise NotImplementedError("Offline mode is not supported")
else:
    asyncio.run(run_migrations_online())