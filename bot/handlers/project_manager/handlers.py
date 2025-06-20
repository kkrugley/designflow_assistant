# file: bot/handlers/project_manager/handlers.py

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.exceptions import TelegramBadRequest

# Импортируем FSM, клавиатуры, модели, сервисы и функции БД
from .fsm import AddProjectIdea, ActivateProject, EditProject
from .keyboards import (
    get_project_manager_keyboard, 
    get_reminder_keyboard, 
    get_project_card_keyboard,
    get_moodboard_choice_keyboard,
    get_edit_project_keyboard,
    get_skip_photo_keyboard
)
from bot.db.models import StatusEnum, Project, AssetTypeEnum
from bot.db.database import (
    create_project_idea, 
    update_project_after_creation, 
    get_projects_by_status,
    get_project_by_id,
    update_project_status,
    delete_project,
    update_project_details,
    add_project_asset,
    get_project_assets
)
from bot.services.notion_service import notion_service
from bot.services.fal_service import generate_moodboard


router = Router()

# =============================================================================
# --- Вспомогательная функция для показа карточки проекта ---
# =============================================================================

async def _show_project_card(message: Message, project_id: int):
    """
    Вспомогательная функция, которая формирует и отправляет "карточку проекта".
    Использует HTML-форматирование и отображает фото.
    """
    project = await get_project_by_id(project_id)
    if not project:
        await message.edit_text("Проект не найден.", reply_markup=get_project_manager_keyboard())
        return
            
    assets = await get_project_assets(project.id)
    reference_image = next((asset for asset in assets if asset.asset_type == AssetTypeEnum.IMAGE_REFERENCE), None)

    notion_url = f"https://www.notion.so/{project.notion_page_id.replace('-', '')}" if project.notion_page_id else None
    
    card_text = (
        f"<b>Проект: {project.name}</b>\n\n"
        f"Статус: <code>{project.status.value}</code>\n\n"
        f"<b>Описание:</b>\n<i>{project.description}</i>"
    )
    
    keyboard = get_project_card_keyboard(project.id, project.status.value, notion_url)

    if reference_image:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer_photo(
            photo=reference_image.telegram_file_id,
            caption=card_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        try:
            await message.edit_text(
                card_text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
        except TypeError:
            await message.answer(
                card_text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )

# =============================================================================
# --- СЦЕНАРИЙ ДОБАВЛЕНИЯ НОВОЙ ИДЕИ ---
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
        "Описание принято. Теперь можете отправить одно фото-референс для идеи или пропустить этот шаг.",
        reply_markup=get_skip_photo_keyboard()
    )
    await state.set_state(AddProjectIdea.waiting_for_photo)

@router.message(AddProjectIdea.waiting_for_photo, F.photo)
async def process_project_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await message.answer(
        "Фото-референс сохранен. Хотите сгенерировать визуальный мудборд?",
        reply_markup=get_moodboard_choice_keyboard()
    )
    await state.set_state(AddProjectIdea.waiting_for_moodboard_choice)

@router.callback_query(AddProjectIdea.waiting_for_photo, F.data == "skip_photo")
async def skip_project_photo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Шаг с фото пропущен. Хотите сгенерировать визуальный мудборд?",
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

    user_data = await state.get_data()
    project_name = user_data.get("project_name")
    description = user_data.get("description")
    photo_file_id = user_data.get("photo_file_id")

    new_project = await create_project_idea(name=project_name, description=description)
    
    if photo_file_id:
        await add_project_asset(
            project_id=new_project.id,
            asset_type=AssetTypeEnum.IMAGE_REFERENCE,
            telegram_file_id=photo_file_id
        )

    notion_result = await notion_service.create_project_page(
        name=project_name, status=StatusEnum.IDEA.value, description=description
    )
    
    text_after_creation = f"✅ Идея '<b>{project_name}</b>' сохранена!"
    if notion_result:
        notion_page_id, notion_url = notion_result
        await update_project_after_creation(project_id=new_project.id, notion_page_id=notion_page_id, reminder_interval=0)
        text_after_creation += f"\n\n📄 <a href='{notion_url}'>Открыть страницу в Notion</a>"
    else:
        text_after_creation += "\n\n<i>Не удалось создать страницу в Notion.</i>"

    await callback.message.edit_text(
        text_after_creation,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=get_project_manager_keyboard()
    )
    await state.clear()


# =============================================================================
# --- СЦЕНАРИЙ АКТИВАЦИИ ПРОЕКТА ---
# =============================================================================

@router.callback_query(F.data.startswith("activate_project_"))
async def activate_project_start(callback: CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split("_")[2])
    await state.update_data(project_id=project_id)
    await callback.answer()
    
    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🚀 <b>Как часто мне напоминать об этом проекте?</b>",
        reply_markup=get_reminder_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ActivateProject.waiting_for_reminder)

@router.callback_query(ActivateProject.waiting_for_reminder, F.data.startswith("remind_"))
async def process_activation_reminder(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    interval = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    project_id = user_data.get("project_id")

    project = await update_project_status(project_id, StatusEnum.ACTIVE)
    if project:
        await update_project_after_creation(project.id, project.notion_page_id, interval)

    if project and project.notion_page_id:
        await notion_service.update_page_status(project.notion_page_id, StatusEnum.ACTIVE.value)
    
    await callback.message.edit_text(
        "✅ Проект <b>активирован</b> и взят в работу!", 
        reply_markup=get_project_manager_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await state.clear()


# =============================================================================
# --- ПРОСМОТР СПИСКОВ И УПРАВЛЕНИЕ ---
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
    
    text = f"<b>{title}</b>:" if projects else f"Список '{title}' пока пуст."
    
    try:
        await callback.message.edit_text(text, reply_markup=list_builder.as_markup(), parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=list_builder.as_markup(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("show_project_"))
async def show_project_card_handler_callback(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[2])
    await callback.answer()
    await _show_project_card(callback.message, project_id)


# =============================================================================
# --- СЦЕНАРИЙ РЕДАКТИРОВАНИЯ ПРОЕКТА ---
# =============================================================================

@router.callback_query(F.data.startswith("edit_project_"))
async def edit_project_start(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[2])
    await callback.answer()
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "Что именно вы хотите отредактировать?",
        reply_markup=get_edit_project_keyboard(project_id)
    )

@router.callback_query(F.data.startswith("edit_name_"))
async def edit_project_name_start(callback: CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split("_")[2])
    project = await get_project_by_id(project_id)
    await state.update_data(project_id=project_id)
    
    await callback.answer()
    await callback.message.edit_text(
        f"Текущее название: <code>{project.name}</code>\n\nВведите новое:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(EditProject.editing_name)

@router.message(EditProject.editing_name, F.text)
async def process_new_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    project_id = user_data.get("project_id")
    new_name = message.text

    project = await update_project_details(project_id=project_id, name=new_name)
    if project and project.notion_page_id:
        await notion_service.update_page_properties(page_id=project.notion_page_id, name=new_name)
        
    await state.clear()
    # Показываем обновленную карточку проекта, а не просто сообщение
    await _show_project_card(message, project_id)

@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_project_desc_start(callback: CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split("_")[2])
    project = await get_project_by_id(project_id)
    await state.update_data(project_id=project_id)

    await callback.answer()
    await callback.message.edit_text(
        f"Текущее описание:\n<i>{project.description}</i>\n\nВведите новое:",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(EditProject.editing_description)

@router.message(EditProject.editing_description, F.text)
async def process_new_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    project_id = user_data.get("project_id")
    new_description = message.text

    project = await update_project_details(project_id=project_id, description=new_description)
    if project and project.notion_page_id:
        await notion_service.update_page_properties(page_id=project.notion_page_id, description=new_description)
        
    await state.clear()
    # Показываем обновленную карточку проекта
    await _show_project_card(message, project_id)

# =============================================================================
# --- ОСТАЛЬНЫЕ ОБРАБОТЧИКИ УПРАВЛЕНИЯ ПРОЕКТОМ ---
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
    await callback.message.edit_text("🗂 <b>Менеджер Проектов</b>", reply_markup=get_project_manager_keyboard(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("delete_project_"))
async def delete_project_handler(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[2])
    project = await get_project_by_id(project_id)
    
    if project and project.notion_page_id:
        await notion_service.archive_page(project.notion_page_id)
        
    await delete_project(project_id)
    await callback.answer("🗑 Идея удалена.", show_alert=True)
    await callback.message.edit_text("🗂 <b>Менеджер Проектов</b>", reply_markup=get_project_manager_keyboard(), parse_mode=ParseMode.HTML)