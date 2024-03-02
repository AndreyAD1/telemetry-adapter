from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")


@cache
def get_settings():
    return Settings()
