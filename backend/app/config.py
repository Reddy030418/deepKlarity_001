from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Recipe Extractor & Meal Planner"
    app_env: str = "dev"
    api_prefix: str = ""
    database_url: str = Field(default="sqlite:///./recipes.db")
    frontend_url: str = "http://localhost:5173"
    frontend_urls: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def normalized_database_url() -> str:
    """
    Accept common cloud DB URLs like 'postgres://...' and normalize them
    for SQLAlchemy psycopg2 driver.
    """
    db_url = settings.database_url.strip()
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return db_url


def allowed_frontend_origins() -> list[str]:
    origins = {settings.frontend_url.strip(), "http://127.0.0.1:5173"}
    if settings.frontend_urls.strip():
        for origin in settings.frontend_urls.split(","):
            cleaned = origin.strip()
            if cleaned:
                origins.add(cleaned)
    return sorted(origins)
