# file: bot/handlers/common.py

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from .project_manager.keyboards import get_project_manager_keyboard
from .template_manager.keyboards import get_automations_menu_keyboard

router = Router()

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
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
    welcome_text = (
        "👋 <b>Привет! Я твой персональный ассистент, Design-Sidekick Bot.</b>\n\n"
        "Я помогу тебе управлять проектами, автоматизировать рутину и "
        "освободить время для самого главного — творчества.\n\n"
        "С чего начнем?"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    menu_text = "С чего начнем?"
    await callback.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "project_manager")
async def show_project_manager_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🗂 <b>Менеджер Проектов</b>\n\nЗдесь вы можете управлять своими идеями и проектами.",
        reply_markup=get_project_manager_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "automations")
async def show_automations_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "✨ <b>Автоматизации</b>\n\nЗдесь можно генерировать контент и управлять шаблонами.",
        reply_markup=get_automations_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )