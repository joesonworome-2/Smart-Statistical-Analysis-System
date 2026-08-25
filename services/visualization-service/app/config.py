from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "SSAS Visualization Service"

    mongo_uri: str
    mongo_database: str = "ssas"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    upload_directory: str = "/app/storage/uploads"
    visualization_directory: str = "/app/storage/visualizations"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
