from fastapi import Depends
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from app.core.database import get_db_session
from app.utils.users import get_user_with_token


class WebSocketManager:
    """
    Менеджер для управления активными WebSocket соединениями.

    Отслеживает активные соединения и предоставляет методы для их управления,
    включая подключение, отключение, отправку сообщений конкретному пользователю
    или всем подключенным пользователям.
    """

    def __init__(self):
        """
        Инициализирует экземпляр WebSocketManager.
        """
        self.active_websockets: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """
        Принимает WebSocket соединение от пользователя.

        Args:
            user_id (int): Идентификатор пользователя.
            websocket (WebSocket): Экземпляр WebSocket соединения пользователя.
        """
        await websocket.accept()
        self.active_websockets[user_id] = websocket

    async def disconnect(self, user_id: int):
        """
        Отключает WebSocket соединение пользователя.

        Args:
            user_id (int): Идентификатор пользователя.
        """
        self.active_websockets.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: str):
        """
        Отправляет сообщение конкретному пользователю.

        Args:
            user_id (int): Идентификатор пользователя.
            message (str): Сообщение для отправки.
        """
        if user_id in self.active_websockets:
            await self.active_websockets[user_id].send_text(message)

    async def send_to_all(self, message: str):
        """
        Отправляет сообщение всем подключенным пользователям.

        Args:
            message (str): Сообщение для отправки.
        """

        clients = self.active_websockets.values()
        for ws in clients:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")


ws_manager = WebSocketManager()


async def websocket_(websocket: WebSocket, session=Depends(get_db_session)):
    """
    Асинхронная функция для обработки WebSocket соединений.

    Аутентифицирует пользователя, управляет его подключением через WebSocketManager,
    ограничивает частоту отправляемых сообщений и отслеживает отключение.

    Args:
        websocket (WebSocket): Экземпляр WebSocket соединения.
        session (Session, optional): Сессия базы данных, зависимость, внедренная через Depends.

    Raises:
        WebSocketDisconnect: Исключение, если соединение было прервано.
    """
    user = await get_user_with_token(websocket, session)
    await ws_manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(user.id)
