# file: bot/__main__.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.db.database import create_db_and_tables
from bot.middlewares.access import AccessMiddleware
from bot.handlers import main_router
from bot.scheduler import setup_scheduler
from dotenv import load_dotenv

load_dotenv()

async def main():
    """
    Основная функция для запуска бота в режиме long polling.
    Используется для локальной разработки и деплоя на Heroku.
    """
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logging.info("Starting bot in polling mode...")

    # Создание таблиц в БД при первом запуске
    await create_db_and_tables()

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация компонентов
    dp.update.middleware(AccessMiddleware(admin_id=settings.telegram_user_id))
    dp.include_router(main_router)

    # Запуск планировщика
    setup_scheduler(bot)

    # Запуск бота
    try:
        # Сначала удаляем вебхук, если он был установлен ранее
        await bot.delete_webhook(drop_pending_updates=True)
        # Затем запускаем polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")