FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir "setuptools<=80.10.2" && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/media /app/static

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]