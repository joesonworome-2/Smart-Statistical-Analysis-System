from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "SSAS Analysis Service"
    environment: str = "development"

    # MongoDB
    mongo_uri: str
    mongo_database: str = "ssas"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    # Dataset storage
    upload_directory: str = "/app/storage/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
