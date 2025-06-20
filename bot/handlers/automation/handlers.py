# file: bot/handlers/automation/handlers.py

import os
import uuid
import asyncio
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType, BufferedInputFile
from aiogram.utils.media_group import MediaGroupBuilder

from bot.db.database import (
    get_projects_by_status, 
    get_all_templates, 
    get_project_by_id, 
    get_template_by_id
)
from bot.db.models import StatusEnum
from bot.services.pdf_generator import create_project_card_pdf
from bot.services.llm_service import generate_text_from_draft, PDF_CARD_PROMPT, SOCIAL_MEDIA_PROMPT
from .fsm import GenerateContent
from .keyboards import get_project_choice_keyboard, get_template_choice_keyboard

router = Router()

TEMP_IMAGES_DIR = "temp_images"

@router.callback_query(F.data == "generate_content")
async def generate_content_start(callback: CallbackQuery, state: FSMContext):
    archived_projects = await get_projects_by_status(StatusEnum.ARCHIVED)
    await callback.answer()
    await callback.message.edit_text(
        "📄 <b>Генератор контента</b>\n\nВыберите завершенный проект, для которого нужно создать материалы.",
        reply_markup=get_project_choice_keyboard(archived_projects),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(GenerateContent.waiting_for_project_choice)

@router.callback_query(GenerateContent.waiting_for_project_choice, F.data.startswith("gen_project_"))
async def process_project_choice(callback: CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split("_")[2])
    await state.update_data(project_id=project_id)
    
    templates = await get_all_templates()
    if not templates:
        await callback.answer("❌ У вас нет ни одного шаблона PDF! Сначала добавьте его в 'Управлении шаблонами'.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        "Проект выбран. Теперь выберите шаблон для PDF-карточки.",
        reply_markup=get_template_choice_keyboard(templates)
    )
    await state.set_state(GenerateContent.waiting_for_template_choice)

@router.callback_query(GenerateContent.waiting_for_template_choice, F.data.startswith("gen_template_"))
async def process_template_choice(callback: CallbackQuery, state: FSMContext):
    template_id = int(callback.data.split("_")[2])
    await state.update_data(template_id=template_id)
    await callback.answer()
    await callback.message.edit_text("Отлично! Теперь отправьте мне финальные рендеры проекта (до 5 штук). Можно отправить группой.")
    await state.set_state(GenerateContent.waiting_for_images)

@router.message(GenerateContent.waiting_for_images, F.photo)
async def process_images(message: Message, state: FSMContext):
    os.makedirs(TEMP_IMAGES_DIR, exist_ok=True)
    file = await message.bot.get_file(message.photo[-1].file_id)
    file_name = f"{uuid.uuid4()}.jpg"
    destination = os.path.join(TEMP_IMAGES_DIR, file_name)
    await message.bot.download_file(file.file_path, destination)
    
    data = await state.get_data()
    image_paths = data.get("image_paths", [])
    image_paths.append(destination)
    await state.update_data(image_paths=image_paths)

    await message.answer(f"Принято фото <b>{len(image_paths)}/5</b>. Когда закончите, отправьте мне дополняющий текст о деталях реализации проекта.", parse_mode=ParseMode.HTML)
    await state.set_state(GenerateContent.waiting_for_draft_text)

@router.message(GenerateContent.waiting_for_draft_text, F.text)
async def process_draft_text_and_generate(message: Message, state: FSMContext):
    await message.answer("<i>Принял! Начинаю генерацию... Это может занять до минуты.</i>", parse_mode=ParseMode.HTML)
    
    user_data = await state.get_data()
    final_draft = message.text
    
    project = await get_project_by_id(user_data.get("project_id"))
    template = await get_template_by_id(user_data.get("template_id"))
    
    initial_description = project.description
    full_draft = f"Initial Idea: {initial_description}\n\nImplementation Details: {final_draft}"
    
    try:
        pdf_text_task = asyncio.create_task(generate_text_from_draft(PDF_CARD_PROMPT, full_draft))
        social_text_task = asyncio.create_task(generate_text_from_draft(SOCIAL_MEDIA_PROMPT, full_draft))
        pdf_text_result, social_text_result = await asyncio.gather(pdf_text_task, social_text_task)
        
        if not pdf_text_result or not social_text_result:
            raise ValueError("Одна или обе LLM задачи вернули ошибку.")

        await message.answer("Тексты сгенерированы. Создаю PDF-файл...")
        
        pdf_bytes = await create_project_card_pdf(
            project_name=project.name,
            project_description=pdf_text_result,
            images_paths=user_data.get("image_paths", []),
            html_template_str=template.html_template,
            css_template_str=template.css_template
        )
        
        pdf_file = BufferedInputFile(pdf_bytes, filename=f"{project.name.replace(' ', '_')}_Card.pdf")
        await message.answer_document(pdf_file, caption="✅ Готово! Ваша презентационная карточка.")
        
        await message.answer(
            f"Текст для социальных сетей:\n<pre>{social_text_result}</pre>",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        await message.answer(f"❌ <b>Произошла серьезная ошибка во время генерации:</b> {e}", parse_mode=ParseMode.HTML)
    finally:
        for path in user_data.get("image_paths", []):
            if os.path.exists(path):
                os.remove(path)
        await state.clear()