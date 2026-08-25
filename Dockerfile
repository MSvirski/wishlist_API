# Испольуем полный образ, где уже есть gcc, make и все библиотеки
FROM python:3.11

WORKDIR /app

# Копируем и ставим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь остальной код проекта в контейнер
COPY . .

# 6. Указываем команду для запуска сервера при старте контейнера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
