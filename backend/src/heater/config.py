from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    evolution_url: str
    evolution_api_key: str
    jwt_secret: str
    redis_url: str

    class Config:
        env_file = ".env"

settings = Settings()
