# file: bot/db/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bot.config import settings
from .models import Base
from .models import Project, StatusEnum
from .models import PdfTemplate
from .models import ProjectAsset, AssetTypeEnum
from sqlalchemy import select

# Создаем асинхронный "движок" для работы с БД
# echo=True полезно для отладки, чтобы видеть генерируемые SQL-запросы
engine = create_async_engine(settings.db_url, echo=True)

# Создаем фабрику асинхронных сессий
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    """
    Функция для создания всех таблиц в базе данных.
    Вызывается один раз при старте приложения.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_project_idea(name: str, description: str = None) -> Project:
    """
    Создает новую запись проекта в статусе 'Идея' в базе данных.
    """
    async with async_session_factory() as session:
        new_project = Project(
            name=name,
            description=description,
            status=StatusEnum.IDEA
        )
        session.add(new_project)
        await session.commit()
        await session.refresh(new_project)
        return new_project

async def update_project_after_creation(project_id: int, notion_page_id: str, reminder_interval: int) -> None:
    """Обновляет проект после создания, добавляя ID Notion и интервал напоминания."""
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            project.notion_page_id = notion_page_id
            if reminder_interval > 0:
                project.reminder_interval_days = reminder_interval
            await session.commit()

async def get_projects_by_status(status: StatusEnum) -> list[Project]:
    """Возвращает список проектов по заданному статусу."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Project).where(Project.status == status).order_by(Project.created_at.desc())
        )
        return result.scalars().all()

async def update_project_status(project_id: int, new_status: StatusEnum):
    """Обновляет статус проекта."""
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            project.status = new_status
            await session.commit()
            return project
    return None

async def delete_project(project_id: int):
    """Удаляет проект из базы данных."""
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            await session.delete(project)
            await session.commit()

async def get_project_by_id(project_id: int) -> Project | None:
    """Возвращает один проект по его ID."""
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        return project
    
async def add_pdf_template(name: str, html_content: str, css_content: str = None):
    """Добавляет новый шаблон PDF в базу данных."""
    async with async_session_factory() as session:
        new_template = PdfTemplate(
            name=name,
            html_template=html_content,
            css_template=css_content
        )
        session.add(new_template)
        await session.commit()

async def get_all_templates() -> list[PdfTemplate]:
    """Возвращает все сохраненные шаблоны PDF."""
    async with async_session_factory() as session:
        result = await session.execute(select(PdfTemplate).order_by(PdfTemplate.name))
        return result.scalars().all()
    
async def get_template_by_id(template_id: int) -> PdfTemplate | None:
    """Возвращает один шаблон PDF по его ID."""
    async with async_session_factory() as session:
        template = await session.get(PdfTemplate, template_id)
        return template
    
async def update_project_details(project_id: int, name: str = None, description: str = None):
    """Обновляет название и/или описание проекта."""
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            if name:
                project.name = name
            if description:
                project.description = description
            await session.commit()
            return project
    return None

async def add_project_asset(project_id: int, asset_type: AssetTypeEnum, telegram_file_id: str):
    """Добавляет ассет (например, фото) к проекту."""
    async with async_session_factory() as session:
        new_asset = ProjectAsset(
            project_id=project_id,
            asset_type=asset_type,
            telegram_file_id=telegram_file_id
        )
        session.add(new_asset)
        await session.commit()

async def get_project_assets(project_id: int) -> list[ProjectAsset]:
    """Возвращает все ассеты для указанного проекта."""
    async with async_session_factory() as session:
        query = select(ProjectAsset).where(ProjectAsset.project_id == project_id)
        result = await session.execute(query)
        return result.scalars().all()