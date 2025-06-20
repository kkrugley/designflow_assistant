# file: bot/handlers/template_manager/handlers.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Document

from .fsm import AddTemplate
from .keyboards import get_template_manager_keyboard, get_skip_css_keyboard
from bot.db.database import add_pdf_template, get_all_templates

router = Router()

@router.callback_query(F.data == "manage_templates")
async def manage_templates_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🎨 **Управление шаблонами**",
        reply_markup=get_template_manager_keyboard()
    )

@router.callback_query(F.data == "list_templates")
async def list_templates_handler(callback: CallbackQuery):
    templates = await get_all_templates()
    if not templates:
        text = "У вас пока нет ни одного шаблона."
    else:
        template_list = "\n".join([f"▪️ `{t.name}`" for t in templates])
        text = f"**Сохраненные шаблоны:**\n\n{template_list}"
    
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=get_template_manager_keyboard())

# --- СЦЕНАРИЙ ДОБАВЛЕНИЯ ШАБЛОНА ---

@router.callback_query(F.data == "add_template")
async def add_template_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Введите уникальное имя для нового шаблона.")
    await state.set_state(AddTemplate.waiting_for_name)

@router.message(AddTemplate.waiting_for_name, F.text)
async def process_template_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично. Теперь отправьте мне HTML-файл шаблона.")
    await state.set_state(AddTemplate.waiting_for_html)

@router.message(AddTemplate.waiting_for_html, F.document)
async def process_template_html(message: Message, state: FSMContext):
    if not message.document.file_name.endswith('.html'):
        await message.answer("Пожалуйста, отправьте файл с расширением .html")
        return
        
    file = await message.bot.get_file(message.document.file_id)
    html_content_bytes = await message.bot.download_file(file.file_path)
    html_content = html_content_bytes.read().decode('utf-8')
    
    await state.update_data(html=html_content)
    await message.answer(
        "HTML-файл принят. Теперь отправьте CSS-файл. Если CSS уже встроен в HTML, нажмите 'Пропустить'.",
        reply_markup=get_skip_css_keyboard()
    )
    await state.set_state(AddTemplate.waiting_for_css)
    
async def save_template(message: Message, state: FSMContext):
    """Вспомогательная функция для сохранения шаблона и завершения FSM."""
    user_data = await state.get_data()
    try:
        await add_pdf_template(
            name=user_data.get("name"),
            html_content=user_data.get("html"),
            css_content=user_data.get("css") # Будет None, если CSS пропущен
        )
        await message.answer(f"✅ Шаблон '{user_data.get('name')}' успешно сохранен!", reply_markup=get_template_manager_keyboard())
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при сохранении: {e}\n\nВозможно, имя шаблона не уникально.", reply_markup=get_template_manager_keyboard())
    
    await state.clear()

@router.message(AddTemplate.waiting_for_css, F.document)
async def process_template_css(message: Message, state: FSMContext):
    if not message.document.file_name.endswith('.css'):
        await message.answer("Пожалуйста, отправьте файл с расширением .css")
        return
        
    file = await message.bot.get_file(message.document.file_id)
    css_content_bytes = await message.bot.download_file(file.file_path)
    css_content = css_content_bytes.read().decode('utf-8')
    await state.update_data(css=css_content)
    await save_template(message, state)

@router.callback_query(AddTemplate.waiting_for_css, F.data == "skip_css")
async def skip_template_css(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await save_template(callback.message, state)