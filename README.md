# Fusion Messenger

Современный веб-мессенджер с поддержкой текстовых сообщений и медиа-файлов.

## Возможности

- Приватные и групповые чаты
- Отправка текстовых сообщений в реальном времени через WebSocket
- Загрузка и отправка медиа-файлов:
  - Изображения (jpg, png, gif, webp)
  - Аудио (mp3, wav, ogg)
  - Документы (pdf, doc, docx, txt)
- Автоматическая очистка хранилища при достижении лимита 1ГБ
- Ограничение размера файла: 10МБ
- Темная тема
- Аутентификация через JWT токены

## Технологический стек

### Бэкенд
- **FastAPI** - Python веб-фреймворк
- **SQLModel** - ORM для SQLite
- **WebSocket** - для real-time сообщений
- **JWT** - аутентификация

### Фронтенд
- **Vue 3** - фреймворк
- **Vite** - сборщик
- **Axios** - HTTP клиент

### Инфраструктура
- **Docker Compose** - контейнеризация
- **Traefik** - reverse proxy с автоматическим HTTPS

## Локальная разработка

### Требования
- Python 3.12+
- Node.js 18+
- Docker и Docker Compose

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd messenger

# 2. Создать .env файл
cp .env.example .env

# 3. Запустить через Docker Compose
docker compose up -d
```

### Доступ после запуска
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Первый пользователь
Создается автоматически при первом запуске. Данные из `.env`:
- Email: `admin@example.com`
- Пароль: `changethis` (изменить в `.env`)

### Запуск без Docker

#### Бэкенд
```bash
cd backend

# Установить зависимости
pip install -e .

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Фронтенд
```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev
```

## Продакшн

### Требования
- Docker и Docker Compose
- Traefik с настроенным HTTPS
- Домен

### Настройка

1. Скопируйте и настройте `.env`:
```bash
cp .env.example .env
```

2. Отредактируйте переменные:
```env
DOMAIN=example.com
STACK_NAME=fusion
DOCKER_IMAGE_BACKEND=your-registry/backend
DOCKER_IMAGE_FRONTEND=your-registry/frontend
SECRET_KEY=<сгенерированный_ключ>
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=<безопасный_пароль>
```

3. Соберите и запустите:
```bash
# Собрать образы
docker compose build

# Запустить
docker compose up -d
```

### Структура сервисов
- `dashboard.example.com` - Frontend
- `api.example.com` - Backend API

## Структура проекта

```
messenger/
├── backend/
│   ├── app/
│   │   ├── api/routes/    # API эндпоинты
│   │   ├── core/          # Конфигурация, БД
│   │   └── models.py      # Модели данных
│   ├── pyproject.toml     # Зависимости Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/        # Vue компоненты
│   │   ├── services/     # API клиент, WebSocket
│   │   └── style.css     # Стили
│   ├── package.json      # Зависимости Node.js
│   └── Dockerfile
├── docker-compose.yml    # Конфигурация Docker
└── .env                  # Переменные окружения
```

## API Endpoints

### Аутентификация
- `POST /api/v1/login/access-token` - Вход
- `POST /api/v1/users/signup` - Регистрация
- `GET /api/v1/users/me` - Текущий пользователь

### Чаты
- `GET /api/v1/chats/` - Список чатов
- `POST /api/v1/chats/private/{user_id}` - Создать приватный чат
- `POST /api/v1/chats/group` - Создать групповой чат
- `GET /api/v1/chats/{chat_id}/messages` - Сообщения чата

### Медиа
- `POST /api/v1/media/upload` - Загрузить файл
- `POST /api/v1/media/{chat_id}` - Отправить сообщение с медиа

### WebSocket
- `WS /api/v1/ws/{chat_id}` - Real-time соединение для чата

## Лимиты

- Размер файла: 10 МБ
- Размер хранилища: 1 ГБ (автоматическая очистка старых файлов)
- Текст сообщения: до 4096 символов

## Лицензия

MIT License