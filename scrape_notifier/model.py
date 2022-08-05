import pathlib

import alembic.command
import alembic.config
from sqlalchemy import Column, DateTime, Integer, create_engine
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
    joined = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<User: telegram_id: {self.telegram_id}, "
            "joined: {self.joined.isoformat()}>"
        )


Session = sessionmaker(bind=engine)
