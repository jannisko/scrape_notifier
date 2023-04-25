from datetime import datetime, timedelta
from typing import cast

import toml

from scrape_notifier.model import SentNotification
from scrape_notifier.scrape import Scraper

example_config = toml.load("config-template.toml")
example_scraper = Scraper(
    **example_config["scraper"],
    telegram_token=example_config["telegram"]["token"],
    telegram_admin_users=example_config["telegram"]["admin_ids"],
)


def _simulate_messages(interval: timedelta, runs: int) -> list[SentNotification]:

    history: list[SentNotification] = []
    start = datetime(2022, 1, 1, 8, 0, 0)
    for i in range(runs):
        next_message_time = start + interval * i
        if example_scraper.should_send_message(history, next_message_time):
            history.append(SentNotification(sent_at=next_message_time))

    return history


def test_increasing_timeouts():

    history = _simulate_messages(timedelta(minutes=5), 100)

    timeouts = [
        next_.sent_at - this.sent_at for this, next_ in zip(history, history[1:])
    ]
    timeouts = cast(list[timedelta], timeouts)

    assert len(history) > 0
    print([t.seconds for t in timeouts])
    assert all([next_ > this for this, next_ in zip(timeouts, timeouts[1:])])


def test_always_send_first_message():
    assert example_scraper.should_send_message([], datetime(2022, 1, 1, 8, 0, 0))


def test_ignore_old_history():

    send_time = datetime(2022, 1, 1, 8, 0, 0)
    old_notification = SentNotification(sent_at=send_time - timedelta(days=365))

    # here it should behave as if there was only the most recent notification
    assert example_scraper.should_send_message(
        [old_notification] * 100
        + [SentNotification(sent_at=send_time - timedelta(hours=1))],
        current_time=send_time,
    )
