import pathlib

import alembic.command
import alembic.config
from sqlalchemy import Column, Date, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeMeta, declarative_base, sessionmaker

engine = create_engine("sqlite:///data/db.sqlite")

# set here to help out mypy with type inference
# https://github.com/python/mypy/issues/2477#issuecomment-703142484
Base: DeclarativeMeta = declarative_base()


def migrate():
    pathlib.Path("data").mkdir(exist_ok=True)
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.attributes["configure_logger"] = False
    alembic.command.upgrade(alembic_cfg, "head")


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    joined_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<User: telegram_id: {self.telegram_id}, "
            f"joined: {self.joined_at.isoformat()}>"
        )


class SentNotification(Base):
    """Table storing a history of sent notifications"""

    __tablename__ = "sent_notifications"

    sent_at = Column(DateTime, primary_key=True)
    scrape_target = Column(String, primary_key=True)
    date_found = Column(Date, primary_key=True)
    # user_id = Column(Integer, ForeignKey("users.telegram_id"), primary_key=True)

    # TODO: set cascade
    # user = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<SentNotification: {self.scrape_target=}, {self.date_found=}"
            f", {self.sent_at=}"
        )


Session = sessionmaker(bind=engine)
