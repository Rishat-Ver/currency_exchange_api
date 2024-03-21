from fastapi import Request
from fastapi.responses import JSONResponse
from googletrans import Translator

from .exceptions import BadRequestException, CustomException
from .models import ErrorResponse

translator = Translator()


def translate_details(string: str, request: Request):
    """
    Переводит текст ошибки в язык, указанный в заголовке 'Accept-Language' запроса.

    Args:
        string (str): Строка для перевода.
        request (Request): Запрос от клиента.

    Returns:
        str: Переведенная строка.
    """
    return translator.translate(
        string, dest=request.headers.get("Accept-Language")[:2]
    ).text


async def custom_exception_handler(request: Request, exc: CustomException):
    """
    Обработчик кастомных исключений, возвращающий ответ JSON с информацией об ошибке.

    Args:
        request (Request): Запрос от клиента.
        exc (CustomException): Перехваченное исключение.

    Returns:
        JSONResponse: Ответ с информацией об ошибке.
    """
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
    """
    Обработчик исключений для ошибок запроса, возвращающий ответ JSON с информацией об ошибке.

    Args:
        request (Request): Запрос от клиента.
        exc (BadRequestException): Перехваченное исключение.

    Returns:
        JSONResponse: Ответ с информацией об ошибке.
    """
    error_response = ErrorResponse(
        url=str(request.url),
        error_code=exc.status_code,
        error_details=str(exc.detail),
        error_message=translate_details(str(exc.detail), request),
    )
    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )
