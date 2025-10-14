# file: bot/handlers/project_manager/keyboards.py

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

def get_project_manager_keyboard():
    """Создает клавиатуру для главного меню менеджера проектов."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Добавить идею", callback_data="add_project_idea")
    )
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

def get_project_card_keyboard(project_id: int, status: str):
    """
    Создает универсальную клавиатуру для карточки проекта в зависимости от его статуса.
    """
    builder = InlineKeyboardBuilder()

    # Кнопки для статуса 'idea'
    if status == 'idea':
        builder.row(
            InlineKeyboardButton(text="🚀 Активировать", callback_data=f"activate_project_{project_id}")
        )
    
    # Кнопки для статуса 'active'
    elif status == 'active':
        builder.row(
            InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_project_{project_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_project_{project_id}")
        )
    
    # Кнопки для статуса 'archived'
    # Пока ничего, но можно добавить "Разархивировать" в будущем

    # Кнопка редактирования (для всех, кроме архива)
    if status != 'archived':
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_project_{project_id}")
        )

    
    # Кнопка "Назад" к соответствующему списку
    if status == 'idea':
        back_callback = "list_idea_projects"
    elif status == 'active':
        back_callback = "list_active_projects"
    else: # archived
        back_callback = "list_archived_projects"
        
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=back_callback)
    )

    return builder.as_markup()

def get_edit_project_keyboard(project_id: int):
    """Клавиатура для выбора, что редактировать в проекте."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Название", callback_data=f"edit_name_{project_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Описание", callback_data=f"edit_desc_{project_id}")
    )
    # Кнопка "Назад" к карточке проекта
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к проекту", callback_data=f"show_project_{project_id}")
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

def get_skip_photo_keyboard():
    """Клавиатура с кнопкой для пропуска шага добавления фото."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить шаг ➡️", callback_data="skip_photo")
    )
    return builder.as_markup()