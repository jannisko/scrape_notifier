FROM python:3.9

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction

COPY alembic.ini .
COPY scrape_notifier scrape_notifier

CMD ["./.venv/bin/python", "-u", "scrape_notifier/main.py"]
