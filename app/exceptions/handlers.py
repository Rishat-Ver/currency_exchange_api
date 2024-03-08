from fastapi import Request
from fastapi.responses import JSONResponse
from googletrans import Translator

from app.exceptions import BadRequestException, CustomException, ErrorResponse

translator = Translator()


def translate_details(string: str, request: Request):
    return translator.translate(
        string, dest=request.headers.get("Accept-Language")[:2]
    ).text


async def custom_exception_handler(request: Request, exc: CustomException):
    error_response = ErrorResponse(
        url=str(request.url),
        error_code=exc.status_code,
        error_details=str(exc.detail),
        error_message=translate_details(str(exc.detail), request),
    )
    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )


async def request_exception_handler(request: Request, exc: BadRequestException):
    error_response = ErrorResponse(
        url=str(request.url),
        error_code=exc.status_code,
        error_details=str(exc.detail),
        error_message=translate_details(str(exc.detail), request),
    )
    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )
