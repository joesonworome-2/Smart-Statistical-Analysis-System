from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "ml-service"

    mongo_uri: str
    mongo_database: str = "ssas"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    dataset_storage_path: str = "/app/storage/uploads"
    model_storage_path: str = "/app/storage/models"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
