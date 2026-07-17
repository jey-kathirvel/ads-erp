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

    # Optional so the application can start before payment keys are configured.
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    BOOKING_GST_PERCENT: float = 5.0
    SMTP_HOST: str = "smtp.hostinger.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = "akshatroyalstay@ads-ai.in"
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = True
    SMTP_USE_STARTTLS: bool = False
    SMTP_FROM_EMAIL: str = "akshatroyalstay@ads-ai.in"
    SMTP_FROM_NAME: str = "Akshat Royal Stay"
    SMTP_REPLY_TO: str = "ars.familystay@gmail.com"
    SMTP_TIMEOUT_SECONDS: int = 15

settings = Settings()
