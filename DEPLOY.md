# Деплой Fusion Messenger

## Требования

- Docker 24+
- Docker Compose 2.20+
- Домен с настроенными A-записями

## Быстрый старт

### 1. Настройка DNS

Добавьте A-записи в DNS:
- `paerser2.ru` -> `217.18.61.113`
- `api.paerser2.ru` -> `217.18.61.113`

### 2. Настройка .env

```bash
cp .env.example .env
nano .env
```

Настройте переменные:
```env
# Домен
DOMAIN=paerser2.ru

# Окружение
ENVIRONMENT=production

# Frontend URL
FRONTEND_HOST=https://paerser2.ru

# CORS
BACKEND_CORS_ORIGINS=https://paerser2.ru,https://api.paerser2.ru

# Секретный ключ (сгенерируйте свой)
SECRET_KEY=ваш_секретный_ключ

# Первый суперпользователь
FIRST_SUPERUSER=admin@paerser2.ru
FIRST_SUPERUSER_PASSWORD=your_strong_password

# SQLite путь к БД
SQLITE_DB_PATH=data/app.db
```

### 3. Запуск

```bash
# Собрать и запустить
docker compose -f docker-compose.yml up -d --build
```

## Доступные сервисы

| Сервис | URL |
|--------|-----|
| Frontend | https://paerser2.ru |
| API | https://api.paerser2.ru |
| API Docs | https://api.paerser2.ru/docs |
| Adminer | https://adminer.paerser2.ru |

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

## Структура сервисов

- **Backend**: FastAPI на порту 8000
- **Frontend**: Nginx с Vue 3 на порту 80
- **Traefik**: Reverse proxy с автоматическим HTTPS

## SSL

Traefik автоматически получает сертификаты Let's Encrypt. При первом запуске может потребоваться несколько минут.