from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://applai:applai@localhost:5433/applai"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    resume_storage_dir: str = "./local-storage/resumes"

    voyage_api_key: str = ""
    embedding_model: str = "voyage-3"
    embedding_dimensions: int = 1024


settings = Settings()
