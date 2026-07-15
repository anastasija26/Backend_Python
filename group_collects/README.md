# Group Collects

Django REST Framework API для групповых денежных сборов.

## Возможности

- CRUD REST API для сборов и платежей.
- Стандартная модель пользователя Django.
- Swagger / ReDoc документация.
- JWT-аутентификация через Simple JWT.
- Отправка email через Celery.
- Кэширование GET-ответов через Redis.
- Открытый CORS для API.
- Management command для моковых данных.
- Запуск через Docker Compose.

## Стек

- Django 4.2
- Django REST Framework
- drf-yasg
- djangorestframework-simplejwt
- django-cors-headers
- django-redis
- Celery
- Redis
- PostgreSQL
- Pillow
- gunicorn
- pytest, pytest-django

## Сущности

### Collect

Групповой сбор содержит:
- автора;
- название;
- повод;
- описание;
- планируемую сумму;
- текущую сумму;
- обложку;
- дату и время завершения;
- ленту платежей с суммой, датой и ФИО пользователя.

### Payment

Платёж по сбору содержит:
- сбор;
- пользователя;
- сумму;
- дату и время создания.

## Права доступа

- `GET` — доступен всем.
- `POST` — только аутентифицированным пользователям.
- Обновление/удаление сборов — только автору.
- Обновление/удаление платежей — только владельцу платежа.

## Swagger

- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## API

### Collects

- `GET /api/collects/`
- `POST /api/collects/`
- `GET /api/collects/{id}/`
- `PUT /api/collects/{id}/`
- `PATCH /api/collects/{id}/`
- `DELETE /api/collects/{id}/`

### Payments

- `GET /api/collects/{collect_id}/payments/`
- `POST /api/collects/{collect_id}/payments/`
- `GET /api/payments/{id}/`
- `PUT /api/payments/{id}/`
- `PATCH /api/payments/{id}/`
- `DELETE /api/payments/{id}/`

### JWT

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`

## Запуск через Docker Compose

### 1. Собрать и запустить проект

```bash
docker compose up --build
```

### 2. Применить миграции

```bash
docker compose exec web python manage.py migrate
```

### 3. Создать суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Наполнить БД тестовыми данными

```bash
docker compose exec web python manage.py load_test_data --users=10 --collects=50 --payments=2000
```

### 5. Запустить тесты

```bash
docker compose run --rm test
```

### 6. Остановить проект

```bash
docker compose down
```

## Доступ после запуска

- `http://localhost:8000/` — Swagger.
- `http://localhost:8000/redoc/` — ReDoc.
- `http://localhost:8000/admin/` — админка.
- `http://localhost:8000/api/collects/` — список сборов.

## Дополнительно

- Email отправляются через Celery в фоне.
- Redis используется как брокер задач и как cache backend.
- Изображения удаляются с диска при удалении записи.
- Кэш GET-ответов инвалидируется при изменении данных.