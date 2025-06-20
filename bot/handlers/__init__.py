# file: bot/handlers/__init__.py

from aiogram import Router

from . import common
from .project_manager import handlers as project_manager_handlers
from .template_manager import handlers as template_manager_handlers
from .automation import handlers as automation_handlers


# Создаем главный роутер, который объединит все остальные
main_router = Router()

# Включаем в него роутеры из всех модулей
main_router.include_router(common.router)
main_router.include_router(project_manager_handlers.router)
main_router.include_router(template_manager_handlers.router)
main_router.include_router(automation_handlers.router)


# Здесь в будущем будут добавляться роутеры из automation, template_manager и т.д.
# main_router.include_router(automation_handlers.router)