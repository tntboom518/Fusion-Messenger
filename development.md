# Разработка

## Запуск через Docker Compose

### Быстрый старт
```bash
docker compose up -d
```

### С отслеживанием изменений (autoreload)
```bash
docker compose watch
```

### Проверка логов
```bash
# Все сервисы
docker compose logs

# Конкретный сервис
docker compose logs backend
docker compose logs frontend
```

## Локальная разработка

### Запуск бэкенда без Docker
```bash
cd backend

# Установка зависимостей (с использованием uv)
uv sync

# Или через poetry
poetry install

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск фронтенда без Docker
```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev сервера
npm run dev
```

### Hot Reload
Можно использовать Docker для бэкенда и локальный сервер для фронтенда:

```bash
# Остановить фронтенд в Docker
docker compose stop frontend

# Запустить локально
cd frontend && npm run dev
```

## Конфигурация

### Файл .env
Основные переменные:
```env
# Проект
PROJECT_NAME=Fusion Messenger
DOMAIN=localhost
STACK_NAME=fusion

# Безопасность
SECRET_KEY=<сгенерируйте_свой_ключ>
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=password123

# Домен для фронтенда
FRONTEND_HOST=http://localhost:5173
```

### Генерация SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## URLs для разработки

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Adminer (БД) | http://localhost:8080 |
| Traefik UI | http://localhost:8090 |

## База данных

Проект использует SQLite. База данных находится в:
- Docker: `/app/data/app.db`
- Локально: `backend/app.db`

### Просмотр БД через Adminer
- Server: `db`
- Username: не требуется
- Password: не требуется
- Database: `app.db`

## Структура кода

### Бэкенд
```
backend/app/
├── api/routes/      # API эндпоинты
│   ├── chats.py     # Работа с чатами
│   ├── messages.py # Текстовые сообщения
│   ├── media.py    # Медиа файлы
│   └── websocket.py # WebSocket соединения
├── core/            # Конфигурация
├── crud.py         # Операции с БД
└── models.py       # Модели данных
```

### Фронтенд
```
frontend/src/
├── views/          # Страницы
│   ├── Chat.vue   # Чат
│   └── Home.vue   # Список чатов
├── services/      # API клиент
│   ├── api.js     # Axios
│   └── websocket.js
└── style.css      # Глобальные стили
```

## Тестирование

### Линтинг бэкенда
```bash
cd backend
./scripts/lint.sh
```

### Тесты
```bash
cd backend
./scripts/test.sh
```

## Медиа файлы

Медиа файлы хранятся в:
- Docker: `/app/media`
- Локально: `backend/media`

Лимиты:
- Максимальный размер файла: 10 МБ
- Общий лимит хранилища: 1 ГБ
- При превышении лимита автоматически удаляются старые файлы