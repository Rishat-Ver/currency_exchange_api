from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: int
    error_details: str = None
    error_message: str
    url: str
