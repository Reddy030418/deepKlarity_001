from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Recipe Extractor & Meal Planner"
    app_env: str = "dev"
    api_prefix: str = ""
    database_url: str = Field(default="sqlite:///./recipes.db")
    frontend_url: str = "http://localhost:5173"
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
