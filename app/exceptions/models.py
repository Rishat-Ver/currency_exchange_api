from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Модель для представления информации об ошибке в ответах.

    Attributes:
        error_code (int): HTTP статус код ошибки.
        error_details (str, optional): Описание ошибки.
        error_message (str): Переведенное сообщение об ошибке.
        url (str): URL, по которому был сделан запрос, вызвавший ошибку.
    """

    error_code: int
    error_details: str = None
    error_message: str
    url: str
