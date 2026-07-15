from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str
    APP_ENV: str
    SECRET_KEY: str

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    HOST: str
    PORT: int

    BACKUP_FOLDER: str = "/opt/ads-erp/backups"
    PG_DUMP_PATH: str = "/usr/bin/pg_dump"
    SESSION_MAX_AGE: int = 28800
    SESSION_HTTPS_ONLY: bool = True
    ALLOWED_HOSTS: str = "erp.ads-ai.in,localhost,127.0.0.1"

settings = Settings()
