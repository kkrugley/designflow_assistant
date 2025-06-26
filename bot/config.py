# file: bot/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Класс для хранения и валидации конфигурационных переменных из .env файла.
    """
    # Telegram
    bot_token: str
    telegram_user_id: int
    
    # Cloud Run (опционально)
    cloud_run_url: Optional[str] = None

    # Notion
    notion_api_key: str
    notion_db_id: str
    notion_title_property_name: str
    notion_status_property_name: str
    
    # Generative AI
    llm_api_key: str
    llm_api_endpoint: str
    fal_api_key: str

    # Настройки базы данных
    db_url: str = Field(default="sqlite+aiosqlite:///bot.db", alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra='ignore'
    )

# Создаем глобальный экземпляр настроек
settings = Settings()

# Исправляем URL для асинхронной SQLAlchemy, если это Heroku или Cloud Run
if settings.db_url and "postgres://" in settings.db_url:
    settings.db_url = settings.db_url.replace("postgres://", "postgresql+asyncpg://", 1)