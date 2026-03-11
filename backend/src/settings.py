from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Security

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
    )

    # Server Connect

    BACKEND_HOST: str
    BACKEND_PORT: int

    FRONTEND_HOST: str
    FRONTEND_PORT: int
    FRONTEND_PROTOCOL: str = "http"

    @property
    def FRONTEND_URL(self) -> str:
        return f"{self.FRONTEND_PROTOCOL}://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"

    # Other

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
    )


settings = Settings()