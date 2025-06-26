# file: bot/scheduler.py

from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from bot.db.database import async_session_factory
from bot.db.models import Project, StatusEnum
from sqlalchemy import select

# --- ЗАДАЧА 1: Напоминания по АКТИВНЫМ проектам ---
async def check_active_projects(bot: Bot, user_id: int):
    print(f"[{datetime.now()}] Running ACTIVE projects reminder check...")
    from bot.handlers.project_manager.keyboards import get_project_card_keyboard

    async with async_session_factory() as session:
        query = select(Project).where(
            Project.status == StatusEnum.ACTIVE,
            Project.reminder_interval_days.is_not(None)
        )
        projects_to_check = (await session.execute(query)).scalars().all()

        for project in projects_to_check:
            last_event_time = project.last_reminded_at or project.created_at
            
            if datetime.now() > last_event_time + timedelta(days=project.reminder_interval_days):
                notion_url = f"https://www.notion.so/{project.notion_page_id.replace('-', '')}" if project.notion_page_id else None
                text = (
                    f"👋 <b>Привет! Как продвигается работа над проектом</b>\n"
                    f"<b>'{project.name}'</b>?\n\n"
                    "<i>Не забывай о сроках! 😉</i>"
                )
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=get_project_card_keyboard(project.id, project.status.value, notion_url),
                        parse_mode=ParseMode.HTML
                    )
                    project.last_reminded_at = datetime.now()
                    await session.commit()
                except Exception as e:
                    print(f"Failed to send reminder for active project '{project.name}': {e}")


# --- ЗАДАЧA 2: Еженедельная проверка ИДЕЙ и АКТИВНОСТИ ---
async def weekly_idea_check(bot: Bot, user_id: int):
    print(f"[{datetime.now()}] Running WEEKLY idea check...")
    async with async_session_factory() as session:
        one_week_ago = datetime.now() - timedelta(days=7)
        query = select(Project).where(Project.created_at >= one_week_ago)
        recent_projects_count = len((await session.execute(query)).scalars().all())

        builder = InlineKeyboardBuilder()
        if recent_projects_count == 0:
            text = "🤔 <b>Давно не было новых идей...</b>\n\nПора штурмовать новые горизонты! Может, добавим что-нибудь?"
            builder.row(InlineKeyboardButton(text="💡 Добавить идею!", callback_data="add_project_idea"))
        else:
            text = "✨ <b>Еженедельный дайджест идей!</b>\n\nНе хочешь заглянуть в свой список? Возможно, там затаился твой следующий шедевр!"
            builder.row(InlineKeyboardButton(text="👀 Посмотреть список идей", callback_data="list_idea_projects"))
        
        builder.row(InlineKeyboardButton(text="Напомнить завтра", callback_data="remind_me_tomorrow_ideas"))
        
        try:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Failed to send weekly digest: {e}")


def setup_scheduler(bot: Bot):
    """Настраивает и запускает планировщик, передавая все нужные зависимости."""
    from bot.config import settings
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    scheduler.add_job(check_active_projects, 'interval', hours=6, args=[bot, settings.telegram_user_id])
    scheduler.add_job(weekly_idea_check, 'cron', day_of_week='mon', hour=10, args=[bot, settings.telegram_user_id])
    
    scheduler.start()
    print("Scheduler started.")