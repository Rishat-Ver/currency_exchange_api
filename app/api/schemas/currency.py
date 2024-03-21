from datetime import datetime

from pydantic import BaseModel


class ResponseCurrency(BaseModel):
    """
    Модель ответа API валют, включающая в себя время, источник и котировки.
    """

    time: datetime
    source: str
    quotes: dict
