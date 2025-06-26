# Используем официальный легковесный образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости для WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в контейнер
COPY . .

# Команда для запуска Uvicorn-сервера. Cloud Run будет использовать ее.
CMD ["uvicorn", "bot.webhook:app", "--host", "0.0.0.0", "--port", "8080"]