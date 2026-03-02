from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./greenlight.db"
    secret_key: str = "dev-secret-key-change-in-production"
    anthropic_api_key: str = ""
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173,http://localhost:5175,http://localhost:8080"
    production: bool = False
    app_url: str = "http://localhost:5173"
    sentry_dsn: str = ""

    model_config = {"env_file": ".env"}

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith(("postgresql://", "postgres://"))


settings = Settings()
