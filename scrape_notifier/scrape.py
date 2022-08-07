import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

import requests

from scrape_notifier.model import SentNotification, Session, User
from scrape_notifier.utils import logger


@dataclass
class Scraper(threading.Thread):

    link_template: str
    targets: list[dict[str, Any]]
    max_days_in_future: int
    scrape_interval_seconds: int
    extraction_regex: str
    date_template: str
    message_template: str

    telegram_token: str

    stop_thread: bool = False

    def __post_init__(self):
        threading.Thread.__init__(self, name="scraper")

    # must overwrite hash here so threading works
    # https://stackoverflow.com/a/2134487
    def __hash__(self):
        return hash(id(self))

    def stop(self):
        logger.info("Stopping scraper thread")
        self.stop_thread = True

    def run(self):

        latest_date = datetime.now() + timedelta(days=self.max_days_in_future)

        time_since_last_scrape = self.scrape_interval_seconds

        while not self.stop_thread:
            if time_since_last_scrape >= self.scrape_interval_seconds:
                time_since_last_scrape = 0

                logger.info("scraping all links")

                message = ""
                for target in self.targets:

                    resp = requests.get(self.link_template.format(**target))

                    if match := re.search(self.extraction_regex, resp.text):

                        # use named groups here instead of index
                        date = self.date_template.format(*match.groups())

                        if datetime.strptime(date, "%d.%m.%Y") < latest_date:

                            message += self.message_template.format(**target, date=date)

                if message:
                    logger.info("Found valid scrape target!")

                    url = f"https://api.telegram.org/bot{self.telegram_token}"

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
