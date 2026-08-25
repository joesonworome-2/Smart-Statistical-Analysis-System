from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "SSAS Authentication Service"
    environment: str = "development"

    # MongoDB
    mongo_uri: str
    mongo_database: str = "ssas"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Refresh Token
    refresh_token_expire_days: int = 7

    # Google OAuth
    google_client_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
