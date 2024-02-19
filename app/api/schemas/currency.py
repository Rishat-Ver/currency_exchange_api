from datetime import date, datetime

from pydantic import BaseModel, field_validator


def normalize(name: str) -> str:
    return name.upper()


class Currency(BaseModel):
    name: str

    normalize_name = field_validator("name")(normalize)


class ResponseCurrency(BaseModel):
    time: datetime
    source: str
    quotes: dict
