from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    evolution_url: str
    evolution_api_key: str
    jwt_secret: str
    redis_url: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
