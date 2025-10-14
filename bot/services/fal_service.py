# file: bot/services/fal_service.py

import asyncio
import httpx
from google import genai
from google.genai import types
from bot.config import settings

async def generate_moodboard(original_prompt: str) -> list[str] | None:
    """
    Генерирует мудборд из изображений с помощью Google Imagen API.

    :param original_prompt: Исходный промпт на русском языке.
    :return: Список URL сгенерированных изображений или None в случае ошибки.
    """
    try:
        # Инициализируем клиент Google AI
        client = genai.Client(api_key=settings.google_ai_api_key)

        # Создаем промпт для генерации изображений
        prompt = f"A professional product design visualization of {original_prompt}, clean white background, studio lighting, high quality, photorealistic"

        print(f"Generated prompt: {prompt}")

        # Генерируем изображения
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=4,
                aspect_ratio='1:1',  # Квадратные изображения
                person_generation='allow_adult',  # Разрешаем генерацию людей если нужно
            )
        )

        # Извлекаем URL изображений
        image_urls = []
        for generated_image in response.generated_images:
            # Google Imagen возвращает объекты изображений, но нам нужны URL
            # Для этого нужно сохранить изображения и загрузить их куда-то
            # Пока что возвращаем placeholder URL
            image_urls.append(f"data:image/png;base64,{generated_image.image._image_bytes}")

        return image_urls if image_urls else None

    except Exception as e:
        print(f"Ошибка при генерации мудборда через Google Imagen: {e}")
        return None