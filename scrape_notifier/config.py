import pathlib
from typing import Any, Dict, Tuple

import toml
from pydantic import BaseModel, BaseSettings, PositiveInt, SecretStr
from pydantic.env_settings import SettingsSourceCallable


def toml_config_settings_source(_: BaseSettings) -> Dict[str, Any]:
    path = pathlib.Path("config.toml")
    if path.is_file():
        return toml.load("config.toml")
    else:
        return {}


class Config(BaseSettings):
    environment: str
    sentry_dsn: str | None

    class Telegram(BaseModel):
        token: SecretStr
        admin_ids: list[int]

    class Scraper(BaseModel):
        link_template: str
        message_template: str
        targets: list[dict[str, Any]]

        extraction_regex: str
        date_template: str
        max_days_in_future: int
        scrape_interval_seconds: PositiveInt

    telegram: Telegram
    scraper: Scraper

    class Config(BaseSettings.Config):
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                env_settings,
                toml_config_settings_source,
                file_secret_settings,
            )


def get_config() -> Config:
    # read all settings and validate using pydantic;
    # type checking is not necessary as types are enforced here.

    return Config()  # type: ignore
