# file: bot/handlers/automation/keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from bot.db.models import Project, PdfTemplate

def get_project_choice_keyboard(projects: list[Project]):
    """Создает клавиатуру для выбора проекта из списка."""
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.row(InlineKeyboardButton(text=f"✅ {project.name}", callback_data=f"gen_project_{project.id}"))
    # Добавляем опцию "Добавить вручную" (пока не реализуем)
    builder.row(InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="gen_manual"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="automations"))
    return builder.as_markup()
    
def get_template_choice_keyboard(templates: list[PdfTemplate]):
    """Создает клавиатуру для выбора шаблона PDF."""
    builder = InlineKeyboardBuilder()
    for template in templates:
        builder.row(InlineKeyboardButton(text=f"🎨 {template.name}", callback_data=f"gen_template_{template.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="automations")) # Пока ведет в общее меню
    return builder.as_markup()