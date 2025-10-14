# file: bot/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Класс для хранения и валидации конфигурационных переменных из .env файла.
    """
    # Telegram
    bot_token: str
    telegram_user_id: int

    
    # Generative AI
    llm_api_key: str
    llm_api_endpoint: str = "https://openrouter.ai/api/v1/chat/completions"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Настройки базы данных
    db_url: str = Field(default="sqlite+aiosqlite:///bot.db", alias="DATABASE_URL")

    # Используем SettingsConfigDict для указания источника - файла .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Создаем глобальный экземпляр настроек, который будет использоваться во всем проекте
settings = Settings()

# Исправляем URL для асинхронной SQLAlchemy, если это Heroku
if settings.db_url.startswith("postgres://"):
    settings.db_url = settings.db_url.replace("postgres://", "postgresql+asyncpg://", 1)
