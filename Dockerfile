FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y git

COPY . .

RUN uv sync

CMD ["uv", "run", "uvicorn", "app.main:deephook", "--host", "0.0.0.0", "--port", "8080"]