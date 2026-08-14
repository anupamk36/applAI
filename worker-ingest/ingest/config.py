from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://applai:applai@localhost:5433/applai"

    # Phase 0: hardcoded seed list of public boards to poll, board/account
    # token -> display name. Real source management (add/remove boards,
    # per-user targeting) is Phase 1+.
    greenhouse_boards: dict[str, str] = {
        "stripe": "Stripe",
        "airbnb": "Airbnb",
        "coinbase": "Coinbase",
    }
    lever_accounts: dict[str, str] = {
        "palantir": "Palantir",
        "lever": "Lever",
    }


settings = Settings()
