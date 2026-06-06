# VK Quiz

Платформа для проведения интерактивных викторин в реальном времени.

***


## Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/like-Ocean/VK_quiz
cd vk_quiz
```

### 2. Создай файл `.env`

Скопируй пример и заполни переменные:

```bash
cp .env.example .env
```

Минимальная конфигурация `.env`:

```env
# База данных
DB_NAME=VK_quiz
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=db или 127.0.0.1
DB_PORT=5432

# Приложение
APP_HOST=0.0.0.0
APP_PORT=8000
APP_RELOAD=False
APP_LOG_LEVEL=info
APP_PROTOCOL=http
DEBUG=false

# Администратор (создаётся автоматически при первом запуске)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin123

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Собери и запусти

```bash
docker compose up --build
```

Или в фоновом режиме:

```bash
docker compose up --build -d
```

После запуска:

| Сервис   | Адрес                        |
|----------|------------------------------|
| Фронтенд | http://localhost:5173         |
| Бэкенд   | http://localhost:8000         |
| API docs | http://localhost:8000/docs    |

***

## Что происходит при запуске

1. Поднимается PostgreSQL, ожидается готовность через healthcheck
2. Бэкенд накатывает миграции (`alembic upgrade head`)
3. Инициализируется БД: создаётся администратор, категории и предзаполненные квизы
4. Пункты 2 и 3 занимают какое то время, имейте терпение :)
5. Запускается FastAPI-сервер на `0.0.0.0:8000`
6. Фронтенд раздаётся через Nginx на порту `5173`

***

## Управление

### Остановить контейнеры

```bash
docker compose down
```

### Остановить и удалить все данные (включая БД)

```bash
docker compose down -v
```

### Посмотреть логи

```bash
# Все сервисы
docker compose logs -f

# Только бэкенд
docker compose logs -f backend

# Только база данных
docker compose logs -f db
```

### Пересобрать после изменений в коде

```bash
docker compose up --build
```

***

## Структура сервисов

```
docker-compose.yaml
├── db          — PostgreSQL 15
├── backend     — FastAPI + Python 3.11
└── frontend    — React (собирается через Node, раздаётся Nginx)
```

***

## Учётные данные по умолчанию

После первого запуска автоматически создаётся администратор:

| Поле     | Значение            |
|----------|---------------------|
| Email    | admin@example.com   |
| Пароль   | Admin123            |


***

## Частые проблемы

**Бэкенд не запускается — ошибка подключения к БД**

Убедись, что в `.env` указано `DB_HOST=db`, а не `127.0.0.1` или `localhost` иногда помогает обратная замена.

**Порт уже занят**

Измени маппинг портов в `docker-compose.yaml`:

```yaml
ports:
  - "8001:8000"  # бэкенд на 8001
```