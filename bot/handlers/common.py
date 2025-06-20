# file: bot/handlers/common.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

# Импортируем нашу новую клавиатуру
from .project_manager.keyboards import get_project_manager_keyboard
from .template_manager.keyboards import get_automations_menu_keyboard

# Создаем роутер для этого модуля
router = Router()

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Создает инлайн-клавиатуру для главного меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗂 Менеджер Проектов", callback_data="project_manager")
    )
    builder.row(
        InlineKeyboardButton(text="✨ Автоматизации", callback_data="automations")
    )
    return builder.as_markup()


# --- ХЭНДЛЕРЫ ---

@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и главное меню.
    """
    welcome_text = (
        "👋 **Привет! Я твой персональный ассистент, Design-Sidekick Bot.**\n\n"
        "Я помогу тебе управлять проектами, автоматизировать рутину и "
        "освободить время для самого главного — творчества.\n\n"
        "С чего начнем?"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Обработчик для кнопки "Назад", возвращающей в главное меню.
    """
    # Используем answer_callback_query, чтобы убрать "часики" на кнопке
    await callback.answer()
    
    menu_text = "С чего начнем?"
    # Редактируем сообщение, чтобы меню появилось на месте предыдущего
    await callback.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())

# Пустышки-обработчики для кнопок главного меню
# Они нужны, чтобы бот не "вис" при нажатии на них
@router.callback_query(F.data == "project_manager")
async def show_project_manager_menu(callback: CallbackQuery):
    """Показывает меню менеджера проектов."""
    await callback.answer() # Убираем "часики"
    await callback.message.edit_text(
        "🗂 **Менеджер Проектов**\n\nЗдесь вы можете управлять своими идеями и проектами.",
        reply_markup=get_project_manager_keyboard()
    )

@router.callback_query(F.data == "automations")
async def show_automations_menu(callback: CallbackQuery):
    """Показывает меню автоматизаций."""
    await callback.answer()
    await callback.message.edit_text(
        "✨ **Автоматизации**\n\nЗдесь можно генерировать контент и управлять шаблонами.",
        reply_markup=get_automations_menu_keyboard()
    )