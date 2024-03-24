from fastapi import HTTPException


class CustomException(HTTPException):
    """
    Основное исключение для обработки ошибок в FastAPI приложении.

    Args:
        detail (str): Описание ошибки.
        status_code (int): HTTP статус код ошибки.
    """

    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(CustomException):
    """
    Исключение для обработки ошибок с HTTP статусом 400 (Bad Request).

    Args:
        detail (str): Описание ошибки.
        status_code (int, optional): HTTP статус код ошибки. По умолчанию 400.
    """

    def __init__(self, detail: str, status_code: int = 400):
        self.status_code = status_code
        self.detail = detail
