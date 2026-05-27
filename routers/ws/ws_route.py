from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from core.security import decode_access_token
from services.ws_handler import handle_room_ws

ws_router = APIRouter(tags=["ws"])


@ws_router.websocket("/ws/room/{join_code}")
async def room_ws(websocket: WebSocket, join_code: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        subject_id = decode_access_token(token)
    except JWTError:
        await websocket.close(code=1008)
        return

    await handle_room_ws(websocket, join_code, subject_id)
