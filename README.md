# Ubilling User Bot

Telegram-бот личного кабинета абонента для биллинговой системы [Ubilling](https://ubilling.net.ua/).

## Возможности

- Авторизация через логин/пароль или deep link
- Просмотр баланса и истории платежей
- Оплата онлайн и активация карт оплаты
- Просмотр и смена тарифов
- Тикеты техподдержки
- Заморозка/разморозка аккаунта
- Кредит
- Информация об аккаунте и провайдере
- Мультиязычный интерфейс (uk/ru/en)

## Запуск

### Docker (production)

```bash
cp .env.example .env
# Отредактируйте .env — укажите BOT_TOKEN и UBILLING_URL

docker compose up -d
```

Бот, PostgreSQL и Redis поднимутся автоматически. Миграции БД применяются при старте контейнера.

Логи:

```bash
docker compose logs -f bot
```

Остановка:

```bash
docker compose down
```

### Локально (для разработки)

Требуется Python 3.13+, [uv](https://docs.astral.sh/uv/), запущенные PostgreSQL и Redis.

```bash
# Установка зависимостей
uv sync

# Конфигурация
cp .env.example .env
# Отредактируйте .env — укажите BOT_TOKEN, UBILLING_URL
# и поменяйте хосты на localhost:
#   DATABASE_URL=postgresql+asyncpg://bot:bot@localhost:5432/bot
#   REDIS_URL=redis://localhost:6379/0

# Применение миграций
uv run alembic upgrade head

# Запуск бота
uv run python -m bot
```

## Конфигурация

Все параметры задаются через переменные окружения (файл `.env`):

| Переменная | Описание | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram-бота | — |
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql+asyncpg://bot:bot@postgres:5432/bot` |
| `REDIS_URL` | Строка подключения к Redis | `redis://redis:6379/0` |
| `UBILLING_URL` | URL Ubilling XMLAgent (userstats) | — |
| `UBILLING_UBER_KEY` | MD5 серийного номера (extended auth) | — |
| `SESSION_TTL_HOURS` | Время жизни сессии (-1 = бессрочно) | `-1` |
| `DEFAULT_LOCALE` | Локаль по умолчанию | `uk` |
| `LOG_LEVEL` | Уровень логирования | `DEBUG` |

## Deep link авторизация

Бот поддерживает авторизацию через deep link:

```
https://t.me/<bot_username>?start=<login>-<password_md5>
```

где `<password_md5>` — MD5-хеш пароля пользователя.

## Структура проекта

```
├── src/bot/
│   ├── __main__.py        # Точка входа
│   ├── config.py          # Настройки (pydantic-settings)
│   ├── db/                # Модели и подключение к БД
│   ├── i18n/              # Сервис локализации
│   ├── middlewares/       # Auth и i18n middleware
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Inline-клавиатуры
│   ├── services/          # BillingService
│   ├── states/            # FSM состояния
│   └── utils/             # Пагинация, форматирование
├── locales/               # JSON-файлы локализации (uk, ru, en)
├── alembic/               # Миграции БД
├── Dockerfile             # Multi-stage сборка
└── docker-compose.yml     # Бот + PostgreSQL + Redis
```
