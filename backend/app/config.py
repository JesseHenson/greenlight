from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./coparenting.db"
    secret_key: str = "dev-secret-key-change-in-production"
    anthropic_api_key: str = ""
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    model_config = {"env_file": ".env"}

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith(("postgresql://", "postgres://"))


settings = Settings()
