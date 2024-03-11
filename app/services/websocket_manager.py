from fastapi import Depends, HTTPException
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from fastapi_limiter.depends import WebSocketRateLimiter

from app.core.database import get_db_session
from app.utils.users import get_user_with_token


class WebSocketManager:
    def __init__(self):
        self.active_websockets: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()

        self.active_websockets[user_id] = websocket

    async def disconnect(self, user_id: int):
        self.active_websockets.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: str):
        if user_id in self.active_websockets:
            await self.active_websockets[user_id].send_text(message)

    async def send_to_all(self, message: str):
        clients = self.active_websockets.values()
        for ws in clients:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")


ws_manager = WebSocketManager()


async def websocket_(websocket: WebSocket, session=Depends(get_db_session)):
    user = await get_user_with_token(websocket, session)
    await ws_manager.connect(user.id, websocket)
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                await ratelimit(websocket, context_key=str(user.id))
            except HTTPException:
                await websocket.send_text("message sending limit exceeded")
    except WebSocketDisconnect:
        await ws_manager.disconnect(user.id)
