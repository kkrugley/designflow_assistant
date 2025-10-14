# file: bot/services/fal_service.py

import asyncio
import httpx
from deep_translator import GoogleTranslator

# Шаблон промпта для генерации изображений
IMAGE_PROMPT_TEMPLATE = (
    "A high-resolution, photorealistic product render of a {translated_text}, "
    "modern design, various options, clean background, "
    "professional studio lighting, 8k, photorealism"
)

async def generate_moodboard(original_prompt: str) -> list[str] | None:
    """
    Генерирует мудборд из изображений с помощью SubNP API.

    :param original_prompt: Исходный промпт на русском языке.
    :return: Список URL сгенерированных изображений или None в случае ошибки.
    """
    try:
        # Переводим ключевые слова на английский
        translated_text = GoogleTranslator(source='auto', target='en').translate(original_prompt)
        final_prompt = IMAGE_PROMPT_TEMPLATE.format(translated_text=translated_text)

        # Структура запроса к SubNP API
        payload = {
            "prompt": final_prompt,
            "model": "turbo"
        }

        headers = {
            "Content-Type": "application/json"
        }

        url = "https://subnp.com/api/free/generate"

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Отправляем POST-запрос для запуска генерации
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            # Читаем потоковый ответ
            image_urls = []
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    try:
                        data = httpx.parse_json(line[6:])  # Убираем 'data: ' префикс
                        if data.get('status') == 'complete' and data.get('imageUrl'):
                            image_urls.append(data['imageUrl'])
                            # Собираем до 4 изображений
                            if len(image_urls) >= 4:
                                break
                        elif data.get('status') == 'error':
                            print(f"Ошибка от SubNP API: {data.get('message')}")
                            return None
                    except Exception as parse_error:
                        print(f"Ошибка парсинга ответа: {parse_error}")
                        continue

            return image_urls if image_urls else None

    except Exception as e:
        print(f"Ошибка при генерации мудборда: {e}")
        return None