### Hexlet tests and linter status:
[![Actions Status](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/EvgeniyMsk/devops-engineer-from-scratch-project-313/actions)

## Запуск приложения

### Требования

- [uv](https://docs.astral.sh/uv/)
- Python 3.13+

### Установка зависимостей

```bash
make install
```

### Запуск

```bash
make run
```

Приложение слушает порт **8080**: http://localhost:8080

### Проверка

```bash
curl http://localhost:8080/ping
```

Ожидаемый ответ: `pong`
