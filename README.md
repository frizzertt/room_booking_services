# Room Booking Service (FastAPI + PostgreSQL)

Сервис бронирования переговорок.

Реализован сервис бронирования переговорок с ролями `admin` и `user`, JWT-авторизацией, расписаниями, генерацией слотов и бронированиями.


## Стек

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL (в docker-compose)
- pytest + pytest-cov


## Быстрый старт (Docker)

1. Скопировать env:

```bash
cp .env.example .env
```

2. Поднять сервис и БД:

```bash
docker compose up --build
```

3. Сервис доступен на `http://localhost:8080`.

Проверка:

```bash
curl http://localhost:8080/_info
```


## Локальный запуск без Docker

1. Создать venv и установить зависимости:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

2. Экспортнуть `DATABASE_URL` на локальный Postgres и инициализировать схему:

```bash
export DATABASE_URL='postgresql+psycopg://rbk:rbk@localhost:5432/rbk'
python -m app.db.init_db
```

3. Запустить API:

```bash
uvicorn app.main:app --reload --port 8080
```


## Примеры API

Получить dummy token:

```bash
curl -X POST http://localhost:8080/dummyLogin \
  -H 'Content-Type: application/json' \
  -d '{"role":"admin"}'
```

Создать переговорку:

```bash
curl -X POST http://localhost:8080/rooms/create \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Room 1","capacity":8}'
```

## Принятые допущения

- Для SQLAlchemy используется `create_all` (без Alembic).
- `conferenceLink` реализован как mock-генератор ссылки без внешнего HTTP-сервиса.
