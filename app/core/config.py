import dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresqlSettings(BaseModel):
    """
    Настройки для подключения к базе данных PostgreSQL.

    Атрибуты:
        PORT (int): Порт, на котором запущен сервер PostgreSQL.
        PASSWORD (str): Пароль пользователя PostgreSQL.
        USER (str): Имя пользователя для доступа к базе данных PostgreSQL.
        NAME (str): Название базы данных PostgreSQL, к которой происходит подключение.
        HOST (str): Имя хоста сервера PostgreSQL.
    """

    PORT: int
    PASSWORD: str
    USER: str
    NAME: str
    HOST: str


class AuthSettings(BaseModel):
    """
    Настройки для системы аутентификации.

    Атрибуты:
        KEY (str): Секретный ключ, используемый в процессах аутентификации.
    """

    KEY: str


class CurrencySettings(BaseModel):
    """
    Настройки, связанные с API валют.

    Атрибуты:
        LIST (str): Эндпоинт для списка доступных валют.
        KEY (str): API-ключ для сервиса валют.
        EXCRATES (str): Эндпоинт для текущих обменных курсов.
        CONVERT (str): Эндпоинт для конвертации валют.
        CHANGE (str): Эндпоинт для отслеживания изменения стоимости валют.
        HISTORICAL (str): Эндпоинт для доступа к историческим данным по валюте.
        TIMEFRAME (str): Эндпоинт для данных о валюте за определенный период времени.
    """

    LIST: str
    KEY: str
    EXCRATES: str
    CONVERT: str
    CHANGE: str
    HISTORICAL: str
    TIMEFRAME: str


class EmailSettings(BaseModel):
    """
    Настройки для сервиса электронной почты.

    Атрибуты:
        NAME (str): Имя или адрес электронной почты, используемый для отправки писем.
        PASS (str): Пароль для доступа к сервису электронной почты.
    """

    NAME: str
    PASS: str


class Settings(BaseSettings):
    """
    Агрегированные настройки приложения, загружаемые из переменных окружения.

    Этот класс объединяет все отдельные классы настроек (DB, AUTH, API, EMAIL)
    и загружает их конфигурации из файла .env с использованием `dotenv` и `pydantic_settings`.

    Переменная класса `model_config` используется для указания расположения файла .env
    и разделителя для вложенных переменных окружения.

    Атрибуты:
        DB (PostgresqlSettings): Настройки для базы данных PostgreSQL.
        AUTH (AuthSettings): Настройки аутентификации.
        API (CurrencySettings): Настройки API валют.
        EMAIL (EmailSettings): Настройки сервиса электронной почты.
    """

    DB: PostgresqlSettings
    AUTH: AuthSettings
    API: CurrencySettings
    EMAIL: EmailSettings

    model_config = SettingsConfigDict(
        env_file=dotenv.find_dotenv(".env"),
        env_nested_delimiter="_",
    )


settings = Settings()
