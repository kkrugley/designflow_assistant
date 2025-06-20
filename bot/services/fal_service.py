# file: bot/services/fal_service.py

import asyncio
import httpx
from deep_translator import GoogleTranslator
from bot.config import settings

# Шаблон промпта для генерации изображений
IMAGE_PROMPT_TEMPLATE = (
    "A high-resolution, photorealistic product render of a {translated_text}, "
    "modern design, various options, clean background, "
    "professional studio lighting, 8k, photorealism"
)

async def generate_moodboard(original_prompt: str) -> list[str] | None:
    """
    Генерирует мудборд из 4 изображений с помощью Fal.AI.

    :param original_prompt: Исходный промпт на русском языке.
    :return: Список URL сгенерированных изображений или None в случае ошибки.
    """
    try:
        # Переводим ключевые слова на английский
        translated_text = GoogleTranslator(source='auto', target='en').translate(original_prompt)
        final_prompt = IMAGE_PROMPT_TEMPLATE.format(translated_text=translated_text)
        
        # Структура запроса к fal.run/imagine
        payload = {
            "prompt": final_prompt,
            "num_images": 4, # Запрашиваем 4 изображения
            "model_name": "fal-ai/fast-sdxl" # Используем быструю модель
        }
        
        headers = {
            "Authorization": f"Key {settings.fal_api_key}",
            "Content-Type": "application/json"
        }
        
        url = "https://fal.run/imagine"

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            # API возвращает список словарей, из каждого извлекаем URL
            image_urls = [item['url'] for item in data['images']]
            return image_urls

    except Exception as e:
        print(f"Ошибка при генерации мудборда: {e}")
        return None