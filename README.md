### Hexlet tests and linter status:
[![Actions Status](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions)
[![CI](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml/badge.svg)](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/ci.yml)

## Описание

Сервис сокращения ссылок на Flask + SQLModel + PostgreSQL.

В продакшене UI раздаётся через **Nginx**, а запросы к API проксируются на бэкенд внутри контейнера.
При старте автоматически создаются таблицы в базе данных.

## Развернутое приложение

**Сервис:** https://devops-engineer-from-scratch-project-313-6ccf.onrender.com

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/ping` | Проверка работоспособности |
| GET | `/api/links` | Список всех ссылок |
| POST | `/api/links` | Создание ссылки |
| GET | `/api/links/:id` | Получение ссылки по id |
| PUT | `/api/links/:id` | Обновление ссылки |
| DELETE | `/api/links/:id` | Удаление ссылки |

### Примеры запросов

```bash
# Healthcheck
curl https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/ping

# Список ссылок
curl "https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/api/links?range=[0,10]"

# Создание ссылки
curl -X POST https://devops-engineer-from-scratch-project-313-6ccf.onrender.com/api/links \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/long-url", "short_name": "exmpl"}'
```

## Локальный запуск

### Требования

- [uv](https://docs.astral.sh/uv/)
- Python 3.13+
- PostgreSQL (или строка подключения в `DATABASE_URL`)
- Node.js 22+ (для локального запуска UI)

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/appdb
SENTRY_DSN=https://your-sentry-dsn
PORT=8080
BASE_URL=http://localhost:8080
```

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Строка подключения к PostgreSQL (обязательно) |
| `SENTRY_DSN` | DSN для Sentry (опционально) |
| `PORT` | Порт приложения (по умолчанию `8080`) |
| `BASE_URL` | Базовый URL для формирования `short_url` (по умолчанию `http://localhost:8080`) |

### Установка и запуск

```bash
make install
make run
```

Приложение доступно на http://localhost:8080

```bash
curl http://localhost:8080/ping
```

## Разработка

### Установка зависимостей (CI/Hexlet)

В CI используется цель `setup`, чтобы не создавать локальную виртуальную среду.

```bash
make setup
```

### Запуск UI + API вместе

```bash
make dev FRAMEWORK=flask
```

После запуска:

- UI: http://localhost:5173
- API: http://localhost:8080

### Линтер

```bash
make lint
```

### Тесты

```bash
make test
```

### Сборка пакета

```bash
make build
make package-install
```

### Docker

```bash
docker build -t paas-web-app .
docker run --rm -p 8080:8080 --env-file .env paas-web-app
```

### Docker (prod-like: Nginx + UI + API в одном контейнере)

Контейнер слушает внешний порт через Nginx (внутри контейнера бэкенд работает на 8080).

```bash
docker build -t paas-web-app .
docker run --rm -p 8080:80 --env-file .env paas-web-app
```
