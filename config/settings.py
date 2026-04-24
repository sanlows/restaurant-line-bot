from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    line_channel_secret: str = Field(default="", alias="LINE_CHANNEL_SECRET")
    line_channel_access_token: str = Field(default="", alias="LINE_CHANNEL_ACCESS_TOKEN")
    line_admin_user_id: str = Field(default="", alias="LINE_ADMIN_USER_ID")
    google_sheet_id: str = Field(default="", alias="GOOGLE_SHEET_ID")
    google_service_account_json_path: str = Field(
        default="service_account.json",
        alias="GOOGLE_SERVICE_ACCOUNT_JSON_PATH",
    )
    google_service_account_json: str = Field(default="", alias="GOOGLE_SERVICE_ACCOUNT_JSON")
    google_places_api_key: str = Field(default="", alias="GOOGLE_PLACES_API_KEY")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def service_account_path(self) -> Path:
        return Path(self.google_service_account_json_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
