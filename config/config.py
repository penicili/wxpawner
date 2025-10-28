import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "wxpawner_db"

    # Flag generation
    FLAG_PREFIX: str = "FLAG"
    FLAG_LENGTH: int = 12

    class Config:
        env_file = ".env"


settings = Settings()