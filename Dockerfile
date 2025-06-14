FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y build-essential gcc && \
    pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install --prefix=/install -r requirements.txt

FROM python:3.13-slim

RUN adduser --disabled-password myuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY alembic alembic
COPY alembic.ini alembic.ini
COPY keys keys
COPY src src
COPY .env.example .env.example
COPY main.py main.py
COPY migrate.sh migrate.sh
RUN chmod +x migrate.sh
COPY README.md README.md
COPY requirements.txt requirements.txt

USER myuser

EXPOSE 8000

CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
