# file: bot/services/pdf_generator.py

import io
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Создаем базовую конфигурацию Jinja. 
# FileSystemLoader здесь не используется напрямую, но это хороший задел на будущее.
env = Environment(loader=FileSystemLoader('.'))

async def create_project_card_pdf(
    project_name: str,
    project_description: str,
    images_paths: list[str], # Список путей к локально скачанным изображениям
    html_template_str: str,
    css_template_str: str = None
) -> bytes:
    """
    Генерирует PDF-карточку проекта на основе шаблонов и данных.

    :param project_name: Название проекта.
    :param project_description: Описание для карточки, сгенерированное LLM.
    :param images_paths: Список путей к файлам изображений.
    :param html_template_str: Строка с HTML-шаблоном.
    :param css_template_str: Строка с CSS-шаблоном (опционально).
    :return: PDF-файл в виде байтов.
    """
    # Загружаем HTML-шаблон из строки
    template = env.from_string(html_template_str)
    
    # Рендерим HTML, передавая в него данные
    rendered_html = template.render(
        project_name=project_name,
        project_description=project_description,
        images=images_paths,
        current_date=datetime.now().strftime("%B %d, %Y")
    )

    font_config = FontConfiguration()
    
    # Создаем объект HTML
    html = HTML(string=rendered_html, base_url='.') # base_url='.' важен для локальных файлов

    # Создаем объект CSS, если он предоставлен
    css = CSS(string=css_template_str, font_config=font_config) if css_template_str else None

    # Записываем PDF в байтовый поток в памяти
    pdf_bytes_io = io.BytesIO()
    html.write_pdf(target=pdf_bytes_io, stylesheets=[css] if css else None, font_config=font_config)
    
    # Возвращаем байты из потока
    return pdf_bytes_io.getvalue()