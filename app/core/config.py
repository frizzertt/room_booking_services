from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://rbk:rbk@db:5432/rbk"

    jwt_secret: str = "super-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    admin_dummy_user_id: str = "00000000-0000-0000-0000-000000000001"
    user_dummy_user_id: str = "00000000-0000-0000-0000-000000000002"


settings = Settings()
