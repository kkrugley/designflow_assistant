# file: bot/handlers/project_manager/fsm.py

from aiogram.fsm.state import State, StatesGroup

class AddProjectIdea(StatesGroup):
    """FSM для добавления новой идеи."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_moodboard_choice = State()
    # Шаг с напоминанием отсюда убран!

class ActivateProject(StatesGroup):
    """FSM для активации проекта и установки напоминания."""
    waiting_for_reminder = State()