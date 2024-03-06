import dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresqlSettings(BaseModel):
    PORT: int
    PASSWORD: str
    USER: str
    NAME: str
    HOST: str
    HOSTNAME: str


class AuthSettings(BaseModel):
    KEY: str


class CurrencySettings(BaseModel):
    LIST: str
    KEY: str
    EXCRATES: str
    CONVERT: str
    CHANGE: str
    HISTORICAL: str
    TIMEFRAME: str


class EmailSettings(BaseModel):
    NAME: str
    PASS: str


class Settings(BaseSettings):
    DB: PostgresqlSettings
    AUTH: AuthSettings
    API: CurrencySettings
    EMAIL: EmailSettings

    model_config = SettingsConfigDict(
        env_file=dotenv.find_dotenv(".env"),
        env_nested_delimiter="_",
    )


settings = Settings()
