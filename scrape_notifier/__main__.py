import pathlib
import threading

import click
import sentry_sdk
import toml

from scrape_notifier import model
from scrape_notifier.config import get_config
from scrape_notifier.health import start_healthcheck_endpoint
from scrape_notifier.main import start_telegram_bot
from scrape_notifier.scrape import Scraper
from scrape_notifier.utils import logger


@click.group(help=toml.load("pyproject.toml")["tool"]["poetry"]["description"])
def cli():
    pass


@cli.group(short_help="operations on the persistence db")
def db():
    pass


@db.command(short_help="init/migrate the db")
def migrate():
    model.migrate()


@db.command(short_help="print registered users")
def users() -> None:
    import sqlite3

    import rich.pretty

    with sqlite3.connect("data/db.sqlite") as con:
        cur = con.cursor()
        try:
            cur.execute("select * from users")
            rich.pretty.pprint(cur.fetchall())
        finally:
            cur.close()


@cli.command(short_help="run the scraper and telegram bot")
def start() -> None:
    config = get_config()

    if config.sentry_dsn is not None:
        sentry_sdk.init(
            dsn=config.sentry_dsn,
            environment=config.environment,
        )

    if not pathlib.Path("data/db.sqlite").exists():
        logger.info("Could not find a DB file, creating one from scratch")
        model.migrate()

    scraper = Scraper(
        **config.scraper.dict(),
        telegram_token=config.telegram.token.get_secret_value(),
        telegram_admin_users=config.telegram.admin_ids,
    )

    scraper_thread = threading.Thread(target=scraper.run, name="scraper")
    scraper_thread.start()

    healtcheck_endpoint_thread = threading.Thread(
        target=start_healthcheck_endpoint, name="healthcheck_endpoint"
    )
    healtcheck_endpoint_thread.start()

    start_telegram_bot()

    scraper.stop()
    scraper_thread.join()
    healtcheck_endpoint_thread.join()


if __name__ == "__main__":
    cli()
