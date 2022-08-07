import pathlib
import threading

import click
import toml

from scrape_notifier import model
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


@cli.command(short_help="run the scraper and telegram bot")
def start():

    if not pathlib.Path("data/db.sqlite").exists():
        logger.info("Could not find a DB file, creating one from scratch")
        model.migrate()

    config = toml.load("config.toml")

    scraper = Scraper(**config["scraper"], telegram_token=config["telegram"]["token"])

    scraper_thread = threading.Thread(target=scraper.run, name="scraper")

    scraper_thread.start()
    start_telegram_bot()

    scraper.stop()
    scraper_thread.join()


if __name__ == "__main__":
    cli()
