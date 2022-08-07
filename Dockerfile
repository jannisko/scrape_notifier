FROM python:3.9

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-root

COPY alembic.ini .
COPY scrape_notifier scrape_notifier
# install again to actually install the code as a local package
RUN poetry install --no-dev --no-interaction

ENTRYPOINT [".venv/bin/scrape-notifier"]
