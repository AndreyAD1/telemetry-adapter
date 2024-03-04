from functools import cache

from pydantic import PositiveInt, NonNegativeInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False
    queue_url: str
    endpoint_url: str
    db_url: str
    max_message_number_by_request: PositiveInt
    sqs_visibility_timeout: PositiveInt
    message_wait_time: NonNegativeInt

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@cache
def get_settings() -> Settings:
    return Settings()
