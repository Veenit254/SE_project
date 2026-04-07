from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_PASSWORD: str  # <-- Added this so Pydantic knows it exists
    DATABASE_URL: str
    REDIS_URL: str
    POLYGON_KEY: str = "demo"
    WATCHLIST: list[str] = ["AAPL", "MSFT", "SPY"]

    class Config:
        env_file = "../.env"
        extra = "ignore"  # <-- Tells Pydantic to safely ignore any future extra variables

settings = Settings()