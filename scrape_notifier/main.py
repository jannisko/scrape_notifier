from datetime import datetime

import toml
from telegram import Update
from telegram.ext import Filters, MessageHandler, Updater

from scrape_notifier.model import Session, User
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
                session.add(User(telegram_id=chat_id, joined_at=datetime.now()))
                message.reply_text(
                    "Registered for notifications.\n"
                    "Send another message to stop all notifications."
                )

            session.commit()
    else:
        logger.warning(f"Received update, that wasn't a message: {update.to_dict()}")


def start_telegram_bot():
    updater = Updater(config["telegram"]["token"])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()

    updater.idle()
