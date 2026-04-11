# Fusion Messenger

Веб-мессенджер с поддержкой текстовых сообщений, медиа-файлов и real-time обновлений через WebSocket.

## Возможности

- **Чаты**: Приватные и групповые беседы
- **Сообщения**: Текстовые с поддержкой медиа
- **Real-time**: Мгновенная доставка через WebSocket
- **Медиа**: Изображения, аудио, документы (до 10 МБ)
- **Хранилище**: Автоматическая очистка при лимите 1 ГБ
- **Аутентификация**: JWT токены сроком на 24 часа

## Технологии

| Компонент | Стек |
|----------|------|
| Backend | FastAPI, SQLModel, SQLite, JWT |
| Frontend | Vue 3, Vite, Axios |
| Proxy | Traefik с автоматическим HTTPS |
| Container | Docker Compose |

## Структура проекта

```
messenger/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API эндпоинты
│   │   ├── core/          # Конфигурация, БД
│   │   ├── main.py       # Точка входа
│   │   └── models.py     # Модели данных
│   ├── pyproject.toml    # Зависимости Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/        # Vue компоненты
│   │   ├── services/     # API клиент, WebSocket
│   │   └── style.css    # Стили
│   ├── package.json      # Зависимости Node.js
│   └── Dockerfile
├── docker-compose.yml    # Конфигурация Docker
└── .env                # Переменные окружения
```

## Быстрый старт

### Docker (рекомендуется)

```bash
# Клонировать и настроить
cp .env.example .env
nano .env  # Настройте DOMAIN и SECRET_KEY

# Запустить
docker compose up -d --build
```

### Локальная разработка

**Backend:**
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv sync
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Конфигурация .env

```env
# Домен
DOMAIN=paerser2.ru

# Окружение
ENVIRONMENT=production

# Frontend URL
FRONTEND_HOST=https://paerser2.ru

# CORS
BACKEND_CORS_ORIGINS=https://paerser2.ru,https://api.paerser2.ru

# Секретный ключ (сгенерируйте: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your_secret_key

# Первый суперпользователь
FIRST_SUPERUSER=admin@paerser2.ru
FIRST_SUPERUSER_PASSWORD=your_strong_password

# SQLite путь
SQLITE_DB_PATH=data/app.db
```

## API Endpoints

### Аутентификация

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/login/access-token | Вход (JWT токен) |
| POST | /api/v1/users/signup | Регистрация |
| GET | /api/v1/users/me | Текущий пользователь |
| PATCH | /api/v1/users/me | Обновить профиль |
| DELETE | /api/v1/users/me | Удалить аккаунт |

### Чаты

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/chats/ | Список чатов |
| GET | /api/v1/chats/{id} | Получить чат |
| POST | /api/v1/chats/private/{user_id} | Создать приватный чат |
| POST | /api/v1/chats/group | Создать групповой чат |
| POST | /api/v1/chats/{id}/members | Добавить участников |
| POST | /api/v1/chats/{id}/read | Отметить как прочитанное |
| GET | /api/v1/chats/{id}/messages | Сообщения чата |

### Сообщения

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/messages/{chat_id} | Отправить сообщение |
| PUT | /api/v1/messages/{id} | Редактировать |
| DELETE | /api/v1/messages/{id} | Удалить |

### Медиа

| Метод | Путь | Описание |
|------|------|----------|
| POST | /api/v1/media/upload | Загрузить файл |
| GET | /api/v1/media/files/{filename} | Получить файл |

### WebSocket

```
WS /api/v1/ws/{chat_id}?token={jwt_token}
```

### Пользователи

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/users/search?q={query} | Поиск пользователей |

### Утилиты

| Метод | Путь | Описание |
|------|------|----------|
| GET | /api/v1/utils/health-check/ | Health check |

## Лимиты

- **Файл**: 10 МБ
- **Хранилище**: 1 ГБ (автоочистка)
- **Сообщение**: 4096 символов
- **Токен**: 24 часа
- **Rate limit**: 5 попыток входа/мин

## Безопасность

- Пароли: Bcrypt хеширование
- Аутентификация: JWT (HS256)
- Защита: Path traversal, SQL injection, XSS
- Валидация: Pydantic модели
- Ограничения: Rate limiting, размеры файлов

## Деплой

### Требования

- Docker 24+
- Docker Compose 2.20+
- Домен с A-записями

### DNS настройка

```
A запись: paerser2.ru -> 217.18.61.113
A запись: api.paerser2.ru -> 217.18.61.113
```

### Запуск

```bash
docker compose -f docker-compose.yml up -d --build
```

## Управление

```bash
# Логи
docker compose logs -f

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Обновление
git pull && docker compose up -d --build
```

## Доступ после запуска

| Сервис | URL |
|--------|-----|
| Frontend | https://paerser2.ru |
| API | https://api.paerser2.ru |
| API Docs | https://api.paerser2.ru/docs |
| Adminer | https://adminer.paerser2.ru |

## Лицензия

MIT