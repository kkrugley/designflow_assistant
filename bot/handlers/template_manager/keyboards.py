# file: bot/handlers/template_manager/keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

def get_automations_menu_keyboard():
    """Создает клавиатуру для меню 'Автоматизации'."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 Генератор контента", callback_data="generate_content")
    )
    builder.row(
        InlineKeyboardButton(text="🎨 Управление шаблонами", callback_data="manage_templates")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

def get_template_manager_keyboard():
    """Создает клавиатуру для управления шаблонами."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить шаблон", callback_data="add_template")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Список шаблонов", callback_data="list_templates")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="automations")
    )
    return builder.as_markup()
    
def get_skip_css_keyboard():
    """Клавиатура с кнопкой для пропуска шага загрузки CSS."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить (CSS в HTML)", callback_data="skip_css")
    )
    return builder.as_markup()