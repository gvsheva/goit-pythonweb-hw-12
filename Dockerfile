# syntax=docker/dockerfile:1

FROM python:3.12
RUN pip install poetry==2.1.1
WORKDIR /app
COPY poetry.lock pyproject.toml .
RUN poetry install --no-root
COPY . .
EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["poetry", "run", "fastapi", "run"]
