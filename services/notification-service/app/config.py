from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "notification-service"

    # MongoDB
    mongo_uri: str
    mongo_database: str = "ssas"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    # Email provider
    # Supported values: brevo, smtp
    email_provider: str = "brevo"

    # Brevo HTTPS API
    brevo_api_key: str | None = None
    brevo_sender_email: str | None = None
    brevo_sender_name: str = "SSAS Notifications"

    # Gmail SMTP fallback
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "SSAS Notifications"
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
