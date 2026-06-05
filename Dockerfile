FROM python:3.11-slim

WORKDIR /app

# Установка uv
RUN pip install uv

# Сначала копируем файлы зависимостей для кэширования слоёв
COPY pyproject.toml uv.lock ./

# Установка production-зависимостей строго по lock-файлу
RUN uv sync --frozen --no-dev

# Копируем всё остальное
COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000

# Запускаем всё через uv run – он автоматически подхватывает .venv
CMD ["sh", "-c", "uv run alembic upgrade head && uv run python main.py"]