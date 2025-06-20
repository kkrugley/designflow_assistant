# file: bot/handlers/template_manager/fsm.py
from aiogram.fsm.state import State, StatesGroup

class AddTemplate(StatesGroup):
    waiting_for_name = State()
    waiting_for_html = State()
    waiting_for_css = State()