# file: bot/db/models.py

import datetime
from sqlalchemy import (
    create_engine,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
    Enum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class StatusEnum(enum.Enum):
    """Перечисление для статусов проекта."""
    IDEA = "idea"
    ACTIVE = "active"
    ARCHIVED = "archived"


class AssetTypeEnum(enum.Enum):
    """Перечисление для типов ассетов проекта."""
    IMAGE_REFERENCE = "image_reference"
    FINAL_RENDER = "final_render"
    MOODBOARD_IMAGE = "moodboard_image"
    GENERATED_PDF = "generated_pdf"
    SOCIAL_TEXT = "social_text"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.IDEA)
    reminder_interval_days: Mapped[int] = mapped_column(Integer, nullable=True)
    last_reminded_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())

    assets: Mapped[list["ProjectAsset"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectAsset(Base):
    __tablename__ = "project_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    asset_type: Mapped[AssetTypeEnum] = mapped_column(Enum(AssetTypeEnum))
    telegram_file_id: Mapped[str] = mapped_column(String(255))
    text_content: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    
    project: Mapped["Project"] = relationship(back_populates="assets")


class PdfTemplate(Base):
    __tablename__ = "pdf_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    html_template: Mapped[str] = mapped_column(Text)
    css_template: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())