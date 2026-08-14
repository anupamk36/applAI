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

    anthropic_api_key: str = ""
    # Small/fast per spec §7.1's task-routing table — field resolution is
    # short-context, JSON-out, high call volume. Never route this to a
    # large model (spec's own warning, §7.1).
    field_resolution_model: str = "claude-haiku-4-5-20251001"


settings = Settings()
