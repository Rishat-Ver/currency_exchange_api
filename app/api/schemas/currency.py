from datetime import datetime

from pydantic import BaseModel


class ResponseCurrency(BaseModel):
    time: datetime
    source: str
    quotes: dict
