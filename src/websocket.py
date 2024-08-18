from fastapi import WebSocket


class ConnectionManager:
    """
    Class to manage websocket connections
    """
    def __init__(self):
        # list where stored all actual active connections
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts new websocket and adds it to connections pool"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes websocket from connections pool"""
        self.active_connections.remove(websocket)

    @staticmethod
    async def send_message(message: str, websocket: WebSocket) -> None:
        """Sends message to websocket"""
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        """Broadcast message for all websockets"""
        for connection in self.active_connections:
            await connection.send_text(message)


ws_manager = ConnectionManager()
