# Развертывание

## Требования

- Docker и Docker Compose
- Traefik с настроенным HTTPS (или другой reverse proxy)
- Домен с настроенными DNS записями

## Подготовка

### 1. Настройка DNS

Добавьте A-записи для вашего домена:
- `dashboard.example.com` → IP сервера
- `api.example.com` → IP сервера

### 2. Настройка Traefik

Если Traefik еще не установлен, создайте конфигурацию:

```bash
mkdir -p /root/code/traefik-public/
```

Скопируйте `docker-compose.traefik.yml` и запустите:

```bash
cd /root/code/traefik-public/
docker compose up -d
```

Создайте Docker сеть:
```bash
docker network create traefik-public
```

### 3. Настройка переменных окружения

Создайте `.env` файл:

```env
# Проект
PROJECT_NAME=Fusion Messenger
DOMAIN=example.com
STACK_NAME=fusion
ENVIRONMENT=production

# Безопасность (обязательно измените!)
SECRET_KEY=<сгенерируйте_ключ>
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=<безопасный_пароль>

# Docker образы
DOCKER_IMAGE_BACKEND=your-registry/fusion-backend
DOCKER_IMAGE_FRONTEND=your-registry/fusion-frontend

# Frontend
FRONTEND_HOST=https://dashboard.example.com
```

### Генерация ключей

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Сборка и запуск

### Локальная сборка

```bash
# Сборка образов
docker compose build

# Запуск
docker compose up -d
```

### Использование с Docker registry

```bash
# Пуш образов
docker push your-registry/fusion-backend
docker push your-registry/fusion-frontend

# Запуск на сервере
docker compose up -d
```

## Проверка

После запуска проверьте:

```bash
docker compose ps
docker compose logs -f
```

## URLs после развертывания

| Сервис | URL |
|--------|-----|
| Frontend | https://dashboard.example.com |
| API | https://api.example.com |
| API Docs | https://api.example.com/docs |
| Traefik Dashboard | https://traefik.example.com |
| Adminer | https://adminer.example.com |

## Обновление

```bash
# Остановить
docker compose stop

# Собрать заново
docker compose build

# Запустить
docker compose up -d
```

## Устранение проблем

### Проверка логов
```bash
docker compose logs backend
docker compose logs frontend
```

### Перезапуск сервисов
```bash
docker compose restart
```

### Очистка
```bash
docker compose down        # Остановить
docker compose down -v     # Остановить и удалить volumes
```

## Структура volumes

- `app-db-data` - База данных SQLite
- `app-media-data` - Медиа файлы пользователей

## Резервное копирование

```bash
# База данных
docker cp fusion-messenger-backend-1:/app/data/app.db ./backup/app.db

# Медиа файлы
docker cp fusion-messenger-backend-1:/app/media ./backup/media
```