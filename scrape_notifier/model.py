import alembic.command
import alembic.config
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///db.sqlite")

Base = declarative_base()


def migrate():
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.attributes["configure_logger"] = False
    alembic.command.upgrade(alembic_cfg, "head")


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    joined = Column(DateTime)

    def __repr__(self) -> str:
        return f"<User: telegram_id: {self.telegram_id}, joined: {self.joined.isoformat()}>"


Session = sessionmaker(bind=engine)
