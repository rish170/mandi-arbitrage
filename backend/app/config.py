from pathlib import Path
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./mandi.db"
    DATA_GOV_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("DATA_GOV_API_KEY", "DATAGOV_API_KEY")
    )
    DATAGOV_RESOURCE_ID: str = "9ef84268-d588-465a-a308-a864a43d0070"
    GOOGLE_MAPS_API_KEY: str = ""
    ADMIN_TOKEN: str = "mandi_local_admin_dev_token_2026"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    MAX_RADIUS_KM: int = 150
    PRICE_MAX_AGE_DAYS: int = 3
    TREND_DAYS: int = 7
    DISABLE_RATE_LIMIT: bool = False

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
