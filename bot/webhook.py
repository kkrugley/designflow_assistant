# file: bot/webhook.py
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties # <--- ИСПРАВЛЕННЫЙ ИМПОРТ

from bot.config import settings
from bot.handlers import main_router
from bot.middlewares.access import AccessMiddleware

# Инициализация FastAPI
app = FastAPI(docs_url=None, redoc_url=None)

# Инициализация Aiogram
bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем middleware и роутеры
dp.update.middleware(AccessMiddleware(admin_id=settings.telegram_user_id))
dp.include_router(main_router)

# URL для вебхука
WEBHOOK_PATH = f"/webhook/{settings.bot_token}"

@app.on_event("startup")
async def on_startup():
    # URL, который предоставит Cloud Run. Мы передадим его через переменную окружения.
    if settings.cloud_run_url:
        webhook_url = f"https://{settings.cloud_run_url}{WEBHOOK_PATH}"
        await bot.set_webhook(url=webhook_url)
        print(f"Webhook set to: {webhook_url}")

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

@app.get("/")
def read_root():
    return {"Status": "Bot is running via webhook"}