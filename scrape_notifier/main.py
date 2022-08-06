import re
import threading
import time
from datetime import datetime, timedelta
from typing import cast

import requests
import toml
from telegram import Update
from telegram.ext import Filters, MessageHandler, Updater

from scrape_notifier.model import SentNotification, Session, User
from scrape_notifier.utils import logger

config = toml.load("config.toml")


def echo(update: Update, _):

    if message := update.message:

        chat_id = message.chat.id
        logger.info(f"got message from {message.chat.id}")

        with Session() as session:

            if user := session.query(User).get(chat_id):

                logger.info("removing user from db")
                session.delete(user)
                message.reply_text(
                    "Stopped all notifications.\n"
                    "Send another message to start sending notifications again."
                )
            else:
                logger.info("inserting user into db")
                session.add(User(telegram_id=chat_id, joined=datetime.now()))
                message.reply_text(
                    "Registered for notifications.\n"
                    "Send another message to stop all notifications."
                )

            session.commit()
    else:
        logger.warning(f"Received update, that wasn't a message: {repr(update)}")


def start_telegram_bot():
    updater = Updater(config["telegram"]["token"])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()

    updater.idle()


class Scraper(threading.Thread):

    stop_thread: bool = False

    def __init__(self):
        threading.Thread.__init__(self, name="scraper")

    def stop(self):
        logger.info("Stopping scraper thread")
        self.stop_thread = True

    def run(self):
        scrape_link_template = config["scraper"]["link_template"]

        scrape_targets = config["scraper"]["targets"]

        latest_date = datetime.now() + timedelta(
            days=config["scraper"]["max_days_in_future"]
        )

        time_since_last_scrape = config["scraper"]["scrape_interval_seconds"]

        while not self.stop_thread:
            if time_since_last_scrape >= config["scraper"]["scrape_interval_seconds"]:
                time_since_last_scrape = 0

                logger.info("scraping all links")

                message = ""
                for target in scrape_targets:

                    resp = requests.get(scrape_link_template.format(**target))

                    if match := re.search(
                        config["scraper"]["extraction_regex"], resp.text
                    ):

                        # use named groups here instead of index
                        date = config["scraper"]["date_template"].format(
                            *match.groups()
                        )

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

    @staticmethod
    def should_send_message(
        notification_history: list[SentNotification],
        current_time: datetime,
    ) -> bool:

        # filter out all old notifications
        # TODO: make dependent on scrape_interval
        notification_history = [
            n
            for n in notification_history
            if current_time - n.sent_at < timedelta(days=1)
        ]

        if len(notification_history) > 0:
            notification_times = [n.sent_at for n in notification_history]
            # to handle missing sqlalchemy type hints
            notification_times = cast(list[datetime], notification_times)

            latest_notification = sorted(notification_times)[-1]
            time_since_last_notification = current_time - latest_notification

        else:
            time_since_last_notification = timedelta(0)

        logger.debug(f"{time_since_last_notification=}, {len(notification_history)=}")
        return time_since_last_notification >= len(notification_history) * timedelta(
            minutes=5
        )
