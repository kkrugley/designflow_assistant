# file: bot/handlers/project_manager/handlers.py

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder # Исправленный импорт

# Импортируем FSM, клавиатуры, модели, сервисы и функции БД
from .fsm import AddProjectIdea, ActivateProject
from .keyboards import (
    get_project_manager_keyboard, 
    get_reminder_keyboard, 
    get_project_card_keyboard,
    get_moodboard_choice_keyboard
)
from bot.db.models import StatusEnum, Project
from bot.db.database import (
    create_project_idea, 
    update_project_after_creation, 
    get_projects_by_status,
    get_project_by_id,
    update_project_status,
    delete_project
)
from bot.services.notion_service import notion_service
from bot.services.fal_service import generate_moodboard


router = Router()

# =============================================================================
# --- СЦЕНАРИЙ ДОБАВЛЕНИЯ НОВОЙ ИДЕИ (УПРОЩЕННЫЙ) ---
# =============================================================================

@router.callback_query(F.data == "add_project_idea")
async def add_project_idea_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Введите название для вашей новой идеи.")
    await state.set_state(AddProjectIdea.waiting_for_name)

@router.message(AddProjectIdea.waiting_for_name, F.text)
async def process_project_name(message: Message, state: FSMContext):
    await state.update_data(project_name=message.text)
    await message.answer("Отлично! Теперь пришлите подробное описание идеи.")
    await state.set_state(AddProjectIdea.waiting_for_description)

@router.message(AddProjectIdea.waiting_for_description, F.text)
async def process_project_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Описание принято. Хотите сгенерировать визуальный мудборд?",
        reply_markup=get_moodboard_choice_keyboard()
    )
    await state.set_state(AddProjectIdea.waiting_for_moodboard_choice)

@router.callback_query(AddProjectIdea.waiting_for_moodboard_choice, F.data.startswith("moodboard_"))
async def process_moodboard_choice_and_finish(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if callback.data == "moodboard_yes":
        await callback.message.edit_text("Генерирую мудборд... Это может занять до минуты.")
        user_data = await state.get_data()
        image_urls = await generate_moodboard(user_data.get("description"))
        
        if image_urls:
            media_group = MediaGroupBuilder(caption="Вот несколько визуальных идей:")
            for url in image_urls:
                media_group.add(type="photo", media=url)
            await callback.message.answer_media_group(media=media_group.build())
        else:
            await callback.message.answer("Не удалось сгенерировать мудборд.")

    # --- ЗАВЕРШЕНИЕ СЦЕНАРИЯ ---
    user_data = await state.get_data()
    project_name = user_data.get("project_name")
    description = user_data.get("description")
    
    new_project = await create_project_idea(name=project_name, description=description)
    
    notion_result = await notion_service.create_project_page(
        name=project_name, status=StatusEnum.IDEA.value, description=description
    )
    
    if not notion_result:
        await callback.message.edit_text("Не удалось создать страницу в Notion. Идея сохранена только в боте.")
    else:
        notion_page_id, notion_url = notion_result
        # Обновляем только ID Notion, без напоминания
        await update_project_after_creation(project_id=new_project.id, notion_page_id=notion_page_id, reminder_interval=0)
        await callback.message.edit_text(f"✅ Идея '{project_name}' сохранена!\n\n📄 Страница в Notion: {notion_url}")

    await state.clear()
    await callback.message.answer("Что делаем дальше?", reply_markup=get_project_manager_keyboard())


# =============================================================================
# --- СЦЕНАРИЙ АКТИВАЦИИ ПРОЕКТА ---
# =============================================================================

@router.callback_query(F.data.startswith("activate_project_"))
async def activate_project_start(callback: CallbackQuery, state: FSMContext):
    """Начинает сценарий активации: запрашивает интервал напоминания."""
    project_id = int(callback.data.split("_")[2])
    await state.update_data(project_id=project_id)
    
    await callback.answer()
    await callback.message.edit_text(
        "🚀 Отличный выбор! Как часто мне напоминать вам об этом активном проекте?",
        reply_markup=get_reminder_keyboard()
    )
    await state.set_state(ActivateProject.waiting_for_reminder)

@router.callback_query(ActivateProject.waiting_for_reminder, F.data.startswith("remind_"))
async def process_activation_reminder(callback: CallbackQuery, state: FSMContext):
    """Ловит интервал, активирует проект в БД и Notion, завершает сценарий."""
    await callback.answer()
    interval = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    project_id = user_data.get("project_id")

    # Обновляем статус в нашей БД
    project = await update_project_status(project_id, StatusEnum.ACTIVE)
    # Обновляем интервал напоминания в БД
    if project:
        await update_project_after_creation(project.id, project.notion_page_id, interval)

    # Обновляем статус в Notion
    if project and project.notion_page_id:
        await notion_service.update_page_status(project.notion_page_id, StatusEnum.ACTIVE.value)
    
    await callback.message.edit_text("✅ Проект активирован и взят в работу!", reply_markup=get_project_manager_keyboard())
    await state.clear()


# =============================================================================
# --- ПРОСМОТР СПИСКОВ И КАРТОЧЕК ПРОЕКТОВ (без изменений) ---
# =============================================================================
@router.callback_query(F.data.in_({"list_idea_projects", "list_active_projects", "list_archived_projects"}))
async def list_projects_by_status_handler(callback: CallbackQuery):
    status_map = {
        "list_idea_projects": (StatusEnum.IDEA, "💡 Список идей"),
        "list_active_projects": (StatusEnum.ACTIVE, "⚡️ Активные проекты"),
        "list_archived_projects": (StatusEnum.ARCHIVED, "🗄 Архив")
    }
    status_enum, title = status_map[callback.data]
    projects = await get_projects_by_status(status_enum)
    await callback.answer()

    list_builder = InlineKeyboardBuilder()
    if projects:
        for p in projects:
            list_builder.row(InlineKeyboardButton(text=p.name, callback_data=f"show_project_{p.id}"))
    
    list_builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="project_manager"))
    
    text = f"**{title}**:" if projects else f"Список '{title}' пока пуст."
    await callback.message.edit_text(text, reply_markup=list_builder.as_markup())

@router.callback_query(F.data.startswith("show_project_"))
async def show_project_card_handler(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[2])
    project = await get_project_by_id(project_id)
    await callback.answer()

    if not project:
        await callback.message.edit_text("Проект не найден.", reply_markup=get_project_manager_keyboard())
        return
            
    notion_url = f"https://www.notion.so/{project.notion_page_id.replace('-', '')}" if project.notion_page_id else None
            
    card_text = (
        f"**Проект: {project.name}**\n\n"
        f"Статус: `{project.status.value}`\n\n"
        f"Описание:\n_{project.description}_"
    )
    
    await callback.message.edit_text(
        card_text,
        reply_markup=get_project_card_keyboard(project.id, project.status.value, notion_url),
        disable_web_page_preview=True
    )

# =============================================================================
# --- ОБРАБОТЧИКИ УПРАВЛЕНИЯ ПРОЕКТОМ (без изменений) ---
# =============================================================================
@router.callback_query(F.data.startswith(("complete_project_", "cancel_project_")))
async def archive_project_handler(callback: CallbackQuery):
    action, _, project_id_str = callback.data.partition("_project_")
    project_id = int(project_id_str)
    
    project = await update_project_status(project_id, StatusEnum.ARCHIVED)
    if project and project.notion_page_id:
        await notion_service.update_page_status(project.notion_page_id, StatusEnum.ARCHIVED.value)
            
    alert_text = "✅ Проект завершен и перенесен в архив." if action == "complete" else "❌ Проект отменен и перенесен в архив."
    await callback.answer(alert_text, show_alert=True)
    await callback.message.edit_text("🗂 **Менеджер Проектов**", reply_markup=get_project_manager_keyboard())

@router.callback_query(F.data.startswith("delete_project_"))
async def delete_project_handler(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[2])
    project = await get_project_by_id(project_id)
    
    if project and project.notion_page_id:
        await notion_service.archive_page(project.notion_page_id)
        
    await delete_project(project_id)
    await callback.answer("🗑 Идея удалена.", show_alert=True)
    await callback.message.edit_text("🗂 **Менеджер Проектов**", reply_markup=get_project_manager_keyboard())