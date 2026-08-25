from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "api-gateway"

    auth_service_url: str = "http://auth-service:8001"
    user_service_url: str = "http://user-service:8002"
    dataset_service_url: str = "http://dataset-service:8003"
    analysis_service_url: str = "http://analysis-service:8004"
    statistics_service_url: str = "http://statistics-service:8005"
    ml_service_url: str = "http://ml-service:8006"
    visualization_service_url: str = "http://visualization-service:8007"
    report_service_url: str = "http://report-service:8008"
    notification_service_url: str = "http://notification-service:8009"

    request_timeout: float = 120.0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
