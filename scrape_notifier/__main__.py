import click
import toml

from scrape_notifier.main import Scraper, start_registering_process
from scrape_notifier import model
from utils import logger

import pathlib


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

    t = Scraper()
    t.start()
    start_registering_process()

    t.stop()
    t.join()


if __name__ == "__main__":
    cli()
