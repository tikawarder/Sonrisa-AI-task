from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/alertdb"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/test_alertdb"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    GEMINI_API_KEY: str = ""
    RSS_FEED_URLS: str = "https://feeds.bbci.co.uk/news/rss.xml"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SLACK_BOT_TOKEN: str = ""
    ADMIN_PASSWORD: str = "change-me-admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def rss_feed_list(self) -> list[str]:
        return [url.strip() for url in self.RSS_FEED_URLS.split(",") if url.strip()]


settings = Settings()
