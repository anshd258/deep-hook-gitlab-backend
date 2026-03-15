from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    GITLAB_URL: str
    GITLAB_TOKEN: str
    LOG_LEVEL: str = "INFO"

settings = Settings()
