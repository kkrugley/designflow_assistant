# file: bot/__main__.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.db.database import create_db_and_tables
from bot.middlewares.access import AccessMiddleware
from bot.handlers import main_router # Импортируем главный роутер
from bot.scheduler import setup_scheduler


async def main():
    """
    Основная функция для запуска бота.
    """
    # Настройка логирования для отладки
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logging.info("Starting bot...")

    # Создание сессии с базой данных (если используется SQLAlchemy)
    # и создание таблиц при первом запуске
    await create_db_and_tables()

    # Инициализация бота и диспетчера
    # Используем MemoryStorage для FSM, для начала этого достаточно
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())

    # --- РЕГИСТРАЦИЯ КОМПОНЕНТОВ ---
    
    # 1. Middleware для проверки доступа
    dp.update.middleware(AccessMiddleware(admin_id=settings.telegram_user_id))
    
    # 2. Роутеры
    # Сначала регистрируем общие хэндлеры
    dp.include_router(main_router) # Подключаем главный роутер

    # Здесь в будущем будут добавляться роутеры из других модулей
    # dp.include_router(project_manager.router)
    # dp.include_router(automation.router)
    # ...и так далее

    # --- ЗАПУСК ПЛАНИРОВЩИКА ---
    setup_scheduler(bot)

    # --- ЗАПУСК БОТА ---
    try:
        # Удаляем вебхук, если он был установлен ранее
        await bot.delete_webhook(drop_pending_updates=True)
        # Запускаем polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")