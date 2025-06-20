# file: bot/services/notion_service.py

from notion_client import AsyncClient
from bot.config import settings

class NotionService:
    """
    Сервис для взаимодействия с Notion API.
    """
    def __init__(self):
        self.client = AsyncClient(auth=settings.notion_api_key)
        self.database_id = settings.notion_db_id
        # Считываем имена колонок из настроек
        self.title_prop = settings.notion_title_property_name
        self.status_prop = settings.notion_status_property_name

    async def create_project_page(self, name: str, status: str, description: str = None) -> tuple[str, str] | None:
        """
        Создает новую страницу для проекта в базе данных Notion.
        Возвращает кортеж (ID страницы, URL страницы) или None в случае ошибки.
        """
        parent = {"database_id": self.database_id}
        properties = {
            self.title_prop: {"title": [{"text": {"content": name}}]},
            self.status_prop: {"select": {"name": status}}
        }
        
        payload = {
            "parent": parent,
            "properties": properties,
        }
        
        if description:
            payload["children"] = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": description}}]
                }
            }]

        try:
            page = await self.client.pages.create(**payload)
            return page.get("id"), page.get("url")
        except Exception as e:
            print(f"Ошибка при создании страницы в Notion: {e}")
            return None

    async def update_page_status(self, page_id: str, new_status: str):
        """Обновляет свойство Status на странице Notion."""
        try:
            await self.client.pages.update(
                page_id=page_id,
                properties={self.status_prop: {"select": {"name": new_status}}}
            )
        except Exception as e:
            print(f"Ошибка при обновлении статуса страницы Notion: {e}")
            
    async def update_page_properties(self, page_id: str, name: str = None, description: str = None):
        """Обновляет свойства и контент на странице Notion."""
        try:
            properties_to_update = {}
            if name:
                properties_to_update[self.title_prop] = {"title": [{"text": {"content": name}}]}
            
            # Обновляем свойства (название)
            if properties_to_update:
                await self.client.pages.update(page_id=page_id, properties=properties_to_update)

            # Обновляем контент (описание)
            if description:
                # Сначала получаем все блоки на странице
                blocks_response = await self.client.blocks.children.list(block_id=page_id)
                # Удаляем все существующие параграфы, чтобы заменить их новым
                for block in blocks_response.get('results', []):
                    if block.get('type') == 'paragraph':
                        await self.client.blocks.delete(block_id=block['id'])
                
                # Добавляем новый блок с новым описанием
                await self.client.blocks.children.append(
                    block_id=page_id,
                    children=[{
                        "object": "block", 
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": description}}]}
                    }]
                )
        except Exception as e:
            print(f"Ошибка при обновлении страницы Notion: {e}")

    async def archive_page(self, page_id: str):
        """Архивирует (удаляет) страницу в Notion."""
        try:
            await self.client.pages.update(
                page_id=page_id,
                archived=True
            )
        except Exception as e:
            print(f"Ошибка при архивации страницы Notion: {e}")

# Создаем глобальный экземпляр сервиса для использования в хэндлерах
notion_service = NotionService()