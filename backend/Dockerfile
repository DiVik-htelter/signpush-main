# Используем Python 3.11
FROM python:3.11-slim

# Устанавливаем системные зависимости
# libpq-dev для postgres
# libffi-dev и libssl-dev для gostcrypto
# zlib1g-dev для Pillow/PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала копируем только requirements.txt для кэширования слоев
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]