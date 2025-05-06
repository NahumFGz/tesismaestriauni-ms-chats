import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_NAME: str = os.getenv("DB_NAME", "ms_messaging")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "nahumfg")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "nahumfg")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
