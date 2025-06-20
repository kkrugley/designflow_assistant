# file: bot/handlers/automation/fsm.py
from aiogram.fsm.state import State, StatesGroup

class GenerateContent(StatesGroup):
    waiting_for_project_choice = State()
    waiting_for_template_choice = State()
    waiting_for_images = State()
    waiting_for_draft_text = State()