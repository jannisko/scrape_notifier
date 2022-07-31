from datetime import datetime, timedelta
import re
import threading
import time
import requests
import logging

from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters
import toml

from model import Session, User

config = toml.load("config.toml")

stop_threads = False

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def echo(update: Update, _):
    chat_id = update.message.chat.id
    logger.info(f"got message from {update.message.chat.id}")

    with Session() as session:

        if user := session.query(User).get(chat_id):

            logger.info("removing user from db")
            session.delete(user)
            update.message.reply_text(
                "Stopped all notifications.\nSend another message to start sending notifications again."
            )
        else:
            logger.info("inserting user into db")
            session.add(User(telegram_id=chat_id, joined=datetime.now()))
            update.message.reply_text(
                "Registered for notifications.\nSend another message to stop all notifications."
            )

        session.commit()


def start_registering_process():
    updater = Updater(config["telegram"]["token"])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()

    updater.idle()


def scrape():
    scrape_link_template = config["scraper"]["link_template"]

    scrape_targets = config["scraper"]["targets"]

    latest_date = datetime.now() + timedelta(
        days=config["scraper"]["max_days_in_future"]
    )

    time_since_last_scrape = config["scraper"]["scrape_interval_seconds"]

    while not stop_threads:
        if time_since_last_scrape >= config["scraper"]["scrape_interval_seconds"]:
            time_since_last_scrape = 0

            logger.info("scraping all links")

            message = ""
            for target in scrape_targets:

                resp = requests.get(scrape_link_template.format(**target))

                if match := re.search(config["scraper"]["extraction_regex"], resp.text):

                    # use named groups here instead of index
                    date = config["scraper"]["date_template"].format(*match.groups())

                    if datetime.strptime(date, "%d.%m.%Y") < latest_date:

                        message += config["scraper"]["message_template"].format(
                            **target, date=date
                        )

            if message:
                logger.info("Found valid scrape target!")

                url = f"https://api.telegram.org/bot{config['telegram']['token']}"

                with Session() as session:

                    users = session.query(User).all()

                logger.info(f"sending messages to {len(users)} users")

                for user in users:
                    params = {"chat_id": str(user.telegram_id), "text": message}
                    r = requests.get(url + "/sendMessage", params=params)
                    r.raise_for_status()
            else:
                logger.info("No valid scrape target found.")
        else:
            time.sleep(1)
            time_since_last_scrape += 1


if __name__ == "__main__":

    import alembic.command
    import alembic.config

    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.attributes["configure_logger"] = False
    alembic.command.upgrade(alembic_cfg, "head")

    t = threading.Thread(target=scrape, daemon=True)
    t.start()
    start_registering_process()

    stop_threads = True

    t.join()
