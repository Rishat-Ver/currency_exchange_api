from fastapi import HTTPException


class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(CustomException):
    def __init__(self, detail: str, status_code: int = 400):
        self.status_code = status_code
        self.detail = detail
