# Настройка GitLab CI/CD

## Требования

- GitLab репозиторий
- Сервер для деплоя с SSH доступом
- Docker и Docker Compose на сервере

## Настройка в GitLab

### 1. Переменные (Settings > CI/CD > Variables)

Добавьте следующие защищённые переменные:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CI_REGISTRY_USER` | Пользователь GitLab | ваш_username |
| `CI_REGISTRY_PASSWORD` | Пароль GitLab | xxx |
| `DEPLOY_HOST` | IP сервера | 217.18.61.113 |
| `SSH_PRIVATE_KEY` | Приватный ключ SSH | -----BEGIN RSA PRIVATE KEY... |

### 2. Настройка SSH ключа

На вашем компьютере:
```bash
# Создать ключ
ssh-keygen -t rsa -b 4096 -C "gitlab-ci" -f gitlab-ci-key

# Добавить публичный ключ на сервер
ssh-copy-id -i gitlab-ci-key.pub root@217.18.61.113

# Добавить приватный ключ в GitLab переменные
cat gitlab-ci-key
```

### 3. Настройка Runner (если используете self-hosted)

На сервере с GitLab Runner:
```bash
# Установить GitLab Runner
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
apt-get install gitlab-runner

# ЗарегистрироватьRunner
sudo gitlab-runner register
# URL: https://gitlab.com
# Token: из Settings > CI/CD > Runners
# Executor: docker
# Default image: docker:24-dind
```

## Структура Pipeline

```
stages:
  test (тесты)
  build (сборка образов)
  deploy (деплой на сервер)
```

## Запуск

1. **Push в main** → запускается build (ручной)
2. **Build завершён** → запускается deploy (ручной)
3. **Deploy** → деплоит на сервер

## Команды

```bash
# Запустить pipeline вручную
git push origin main

# Откатить изменения
git revert <commit>
git push origin main
```

## Troubleshooting

### Ошибка "connection refused"
```bash
# Проверить SSH доступ
ssh -v root@217.18.61.113
```

### Ошибка "docker: command not found"
```bash
# Установить Docker на runner
curl -fsSL https://get.docker.com | sh
```

### Ошибка "permission denied"
```bash
# Проверить права на сервере
chmod +x /opt/messenger/deploy.sh
```