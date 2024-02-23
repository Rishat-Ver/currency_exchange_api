from datetime import date, datetime

from pydantic import BaseModel, field_validator


class ResponseCurrency(BaseModel):
    time: datetime
    source: str
    quotes: dict
