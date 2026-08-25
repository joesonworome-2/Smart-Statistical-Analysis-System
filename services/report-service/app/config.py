from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    project_name: str = (
        "SSAS Report Service"
    )

    environment: str = "development"

    mongo_uri: str = (
        "mongodb://mongodb:27017"
    )

    mongo_database: str = "ssas"

    jwt_secret_key: str = (
        "change-this-secret"
    )

    jwt_algorithm: str = "HS256"

    visualization_service_url: str = (
        "http://visualization-service:8007"
    )

    notification_service_url: str = (
        "http://notification-service:8009"
    )

    report_directory: str = (
        "/app/storage/reports"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


Path(
    settings.report_directory
).mkdir(
    parents=True,
    exist_ok=True,
)
