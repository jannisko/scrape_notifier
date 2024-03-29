import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, NamedTuple, cast

import requests

from scrape_notifier.model import SentNotification, Session, User
from scrape_notifier.utils import logger


class ValidTarget(NamedTuple):
    date: date
    target: dict[str, Any]


@dataclass
class Scraper:
    link_template: str
    targets: list[dict[str, Any]]
    max_days_in_future: int
    scrape_interval_seconds: int
    extraction_regex: str
    date_template: str
    message_template: str

    telegram_token: str
    telegram_admin_users: list[int]

    stop_thread: bool = False

    def notify_admins(self, message: str) -> None:
        for admin_id in self.telegram_admin_users:
            params = {
                "chat_id": str(admin_id),
                "text": message,
                "parse_mode": "Markdown",
            }
            url = f"https://api.telegram.org/bot{self.telegram_token}"
            resp = requests.get(url + "/sendMessage", params=params, timeout=60)

            if not resp.ok:
                logger.warning("Couldn't send message to admins. RIP. %s", resp.reason)

    def stop(self):
        logger.info("Stopping scraper thread")
        self.stop_thread = True

    def run(self):
        time_since_last_scrape = self.scrape_interval_seconds

        while not self.stop_thread:
            if time_since_last_scrape >= self.scrape_interval_seconds:
                time_since_last_scrape = 0

                logger.info("scraping all links")

                try:
                    self.scrape_and_notify()
                except Exception as error:
                    logger.error(error)
                    raise error

            else:
                time.sleep(1)
                time_since_last_scrape += 1

    def scrape_and_notify(self):
        latest_date = datetime.now() + timedelta(days=self.max_days_in_future)

        all_scrape_results = self.scrape()

        valid_scrape_results = [
            res for res in all_scrape_results if res.date < latest_date.date()
        ]

        if len(valid_scrape_results) > 0:
            logger.info("Found valid scrape target!")
            self.send_messages(valid_scrape_results)
        else:
            logger.info("No valid scrape target found.")

    def scrape(self) -> list[ValidTarget]:
        results: list[ValidTarget] = []
        for target in self.targets:
            try:
                resp = requests.get(self.link_template.format(**target), timeout=20)
            except requests.exceptions.ConnectionError as error:
                logger.error("Scraping %s threw error: %s", target, error)
                self.notify_admins("Scraping %s threw error: %s" % (target, error))
            except Exception as else_error:
                logger.error(
                    "Scraping %s threw unexpected error: %s", target, else_error
                )
                self.notify_admins(
                    "Scraping %s threw unexpected error: %s" % (target, else_error)
                )
                raise else_error
            else:
                if match := re.search(self.extraction_regex, resp.text):
                    # TODO: use named groups here instead of index
                    found_date = datetime.strptime(
                        self.date_template.format(*match.groups()), "%d.%m.%Y"
                    ).date()

                    results.append(ValidTarget(found_date, target))

        return results

    def send_messages(self, results: list[ValidTarget]):
        with Session() as session:
            non_rate_limited_results = [
                res
                for res in results
                if self.should_send_message(
                    notification_history=session.query(SentNotification)
                    .filter(
                        SentNotification.scrape_target == json.dumps(res.target),
                        SentNotification.date_found == res.date,
                    )
                    .all(),
                    current_time=datetime.now(),
                )
            ]

            logger.info(
                f"Valid targets before rate limiting: {len(results)}, "
                f"after: {len(non_rate_limited_results)}"
            )

            if len(non_rate_limited_results) > 0:
                message = "".join(
                    [
                        self.message_template.format(
                            **res.target, date=res.date.strftime("%d.%m.%Y")
                        )
                        for res in non_rate_limited_results
                    ]
                )

                url = f"https://api.telegram.org/bot{self.telegram_token}"

                users = session.query(User).all()
                users = cast(list[User], users)

                logger.info(f"sending messages to {len(users)} users")

                for user in users:
                    params = {
                        "chat_id": str(user.telegram_id),
                        "text": message,
                        "parse_mode": "Markdown",
                    }
                    r = requests.get(url + "/sendMessage", params=params)

                    if not r.ok:
                        logger.error(
                            f"Message to {user.telegram_id} failed with error: "
                            f"{r.text}"
                        )

                        error_actions: dict[str, Callable[[User], None]] = {
                            "Forbidden:" "bot was blocked by the user": session.delete
                        }

                        if action := error_actions.get(r.json()["description"]):
                            action(user)

                session.add_all(
                    [
                        SentNotification(
                            scrape_target=json.dumps(res[1]),
                            sent_at=datetime.now(),
                            date_found=res.date,
                        )
                        for res in non_rate_limited_results
                    ]
                )
                session.commit()

    def should_send_message(
        self,
        notification_history: list[SentNotification],
        current_time: datetime,
    ) -> bool:
        interval = timedelta(seconds=self.scrape_interval_seconds)

        # filter out all old notifications
        notification_history = [
            n
            for n in notification_history
            if current_time - n.sent_at < (interval * 100)
        ]

        if len(notification_history) > 0:
            time_until_next_send = interval * 2 ** len(notification_history)

            notification_times = [n.sent_at for n in notification_history]
            # to handle missing sqlalchemy type hints
            notification_times = cast(list[datetime], notification_times)

            latest_notification = sorted(notification_times)[-1]
            time_since_last_notification = current_time - latest_notification

        else:
            time_until_next_send = timedelta(0)
            time_since_last_notification = timedelta(0)

        logger.debug(
            f"{time_since_last_notification=}, {len(notification_history)=}"
            f", {time_until_next_send=}"
        )
        return time_since_last_notification >= time_until_next_send
