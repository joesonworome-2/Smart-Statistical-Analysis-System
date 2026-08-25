from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "SSAS Dataset Service"
    environment: str = "development"

    mongo_uri: str
    mongo_database: str = "ssas"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    upload_directory: str = "/app/storage/uploads"
    max_upload_size_mb: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
