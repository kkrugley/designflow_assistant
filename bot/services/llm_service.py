# file: bot/services/llm_service.py

import httpx
from bot.config import settings

# Ваши промпты из ТЗ
PDF_CARD_PROMPT = """Напиши подробное описание проекта промышленного дизайна на основе черновика ниже. Текст должен:
- Использовать позитивный и дружелюбный тон.
- Чётко описать идею проекта, его реализацию и предмет дизайна.
- Объяснить назначение и функцию предмета.
- Включать профессиональную лексику (например: эргономика, материалы, производственный процесс).
- Быть на английском языке уровня B1-B2 (простые предложения, базовые технические термины).
- Иметь структуру:
        - Заголовок проекта (1 строка).
        - Описание идеи (2-3 предложения).
        - Детали реализации (материалы/технологии, 2 предложения).
        - Функциональность предмета (1-2 предложения).
Черновик: [Draft]"""

SOCIAL_MEDIA_PROMPT = """Создай лаконичный текст для соцсетей (TikTok/Instagram) на основе черновика ниже. Текст должен:
- Быть позитивным, дружелюбным и engaging (используй эмодзи 😊).
- Кратко описать идею проекта, предмет дизайна и его функцию.
- Использовать профессиональную лексику упрощённо (например: "эргономичный дизайн", "инновационные материалы").
- Соответствовать английскому уровню B1-B2 (короткие предложения, простые глаголы).
- Укладываться в 2-3 предложения + хэштеги (например: #IndustrialDesign #Innovation + подходящие к проекту хэштеги).
Черновик: [Draft]"""

async def generate_text_from_draft(prompt_template: str, draft: str) -> str | None:
    """
    Генерирует текст с помощью LLM API (Gemini).

    :param prompt_template: Шаблон промпта (PDF_CARD_PROMPT или SOCIAL_MEDIA_PROMPT).
    :param draft: Черновик текста от пользователя.
    :return: Сгенерированный текст или None в случае ошибки.
    """
    # Подставляем черновик в промпт
    final_prompt = prompt_template.replace("[Draft]", draft)

    headers = {
        "Content-Type": "application/json",
    }
    
    # Структура тела запроса для Gemini API
    json_data = {
        "contents": [{
            "parts": [{"text": final_prompt}]
        }]
    }
    
    # URL с ключом API
    url = f"{settings.llm_api_endpoint}?key={settings.llm_api_key}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=json_data)
            response.raise_for_status() # Вызовет исключение для кодов 4xx/5xx
            
            data = response.json()
            # Извлекаем текст из сложной структуры ответа Gemini
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return generated_text.strip()
            
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP при обращении к LLM API: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка при обращении к LLM API: {e}")
        return None
