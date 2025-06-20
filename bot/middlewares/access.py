# file: bot/middlewares/access.py

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class AccessMiddleware(BaseMiddleware):
    """
    Middleware для проверки доступа.
    Пропускает только апдейты от пользователя, чей ID указан в .env.
    """
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Получаем объект пользователя из апдейта
        user = data.get("event_from_user")
        
        # Если пользователя нет или его ID не совпадает с ID администратора
        if user is None or user.id != self.admin_id:
            # Просто не обрабатываем этот апдейт
            return

        # Если проверка пройдена, вызываем следующий хэндлер
        return await handler(event, data)