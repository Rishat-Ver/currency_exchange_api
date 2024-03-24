import aiohttp

from app.core.config import settings


async def http_client(url: str, params: dict | None = None):
    """
    Асинхронный HTTP-клиент для отправки GET-запросов.

    Использует aiohttp для асинхронной отправки GET-запросов к указанному URL.
    Добавляет к запросу заголовок с API-ключом из настроек приложения.
    В случае успешного ответа сервера (код 200), возвращает данные в формате JSON.
    Если сервер возвращает ошибку, генерируется исключение.

    Args:
        url (str): URL адрес, к которому будет отправлен запрос.
        params (dict | None, optional): Словарь параметров запроса. По умолчанию None.

    Returns:
        dict | None: Данные ответа в формате JSON, если запрос успешен. В противном случае None.

    Raises:
        ClientResponseError: Исключение, если сервер возвращает код ошибки.
    """
    headers = {"apikey": settings.API.KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                response.raise_for_status()
                return
