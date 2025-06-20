# file: bot/handlers/project_manager/keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

def get_project_manager_keyboard():
    """Создает клавиатуру для главного меню менеджера проектов."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Добавить идею", callback_data="add_project_idea")
    )
    # ⬇️⬇️⬇️ ДОБАВЛЯЕМ КНОПКУ ⬇️⬇️⬇️
    builder.row(
        InlineKeyboardButton(text="💡 Список идей", callback_data="list_idea_projects")
    )
    builder.row(
        InlineKeyboardButton(text="⚡️ Активные проекты", callback_data="list_active_projects"),
        InlineKeyboardButton(text="🗄 Архив", callback_data="list_archived_projects")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()

# ⬇️⬇️⬇️ New get_idea_management_keyboard ⬇️⬇️⬇️
def get_project_card_keyboard(project_id: int, status: str, notion_page_url: str = None):
    """
    Создает универсальную клавиатуру для карточки проекта в зависимости от его статуса.
    """
    builder = InlineKeyboardBuilder()

    # Кнопки для статуса 'idea'
    if status == 'idea':
        builder.row(
            InlineKeyboardButton(text="🚀 Активировать", callback_data=f"activate_project_{project_id}")
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_project_{project_id}")
        )

    # Кнопки для статуса 'active'
    elif status == 'active':
        builder.row(
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_project_{project_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_project_{project_id}")
        )
    
    # Кнопки для статуса 'archived'
    # Пока ничего, но можно добавить "Разархивировать" в будущем

    # Общая кнопка для всех, у кого есть страница в Notion
    if notion_page_url:
        builder.row(
            InlineKeyboardButton(text="📄 Открыть в Notion", url=notion_page_url)
        )
    
    # Кнопка "Назад" к общему меню менеджера проектов
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="project_manager")
    )

    return builder.as_markup()

def get_reminder_keyboard():
    """Создает клавиатуру для выбора интервала напоминания."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Раз в день", callback_data="remind_1"),
        InlineKeyboardButton(text="Раз в неделю", callback_data="remind_7")
    )
    builder.row(
        InlineKeyboardButton(text="Раз в 2 недели", callback_data="remind_14"),
        InlineKeyboardButton(text="Раз в месяц", callback_data="remind_30")
    )
    builder.row(
        InlineKeyboardButton(text="Без напоминаний", callback_data="remind_0")
    )
    return builder.as_markup()

def get_moodboard_choice_keyboard():
    """Клавиатура для выбора, генерировать мудборд или нет."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, создать мудборд ✨", callback_data="moodboard_yes"),
        InlineKeyboardButton(text="Пропустить ➡️", callback_data="moodboard_no")
    )
    return builder.as_markup()