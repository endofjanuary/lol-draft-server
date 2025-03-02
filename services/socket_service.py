import socketio
import time
import logging
from typing import Dict
from models import Client

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

class SocketService:
    def __init__(self):
        # Simplified Socket.IO server configuration
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            logger=True,
            engineio_logger=True,
            ping_interval=25,
            ping_timeout=60,
            max_http_buffer_size=1e8
        )
        self.clients: Dict[str, Client] = {}

    async def handle_connect(self, sid: str, environ):
        logger.debug(f"Client attempting to connect: {sid}")
        await self.sio.emit('connection_success', {'sid': sid}, room=sid)
        logger.info(f"Client connected: {sid}")

    async def handle_disconnect(self, sid: str):
        if sid in self.clients:
            client = self.clients[sid]
            logger.info(f"Client disconnected: {client.nickname} ({sid}) from game {client.gameCode}")
            del self.clients[sid]
        else:
            logger.info(f"Unknown client disconnected: {sid}")

    async def handle_join_game(self, sid: str, data: dict):
        try:
            # Create client object
            client = Client(
                socketId=sid,
                gameCode=data['gameCode'],
                position='spectator',  # Default position
                joinedAt=int(time.time() * 1000000),
                nickname=data['nickname']
            )
            
            # Store client
            self.clients[sid] = client
            
            logger.info(f"Client joined: {client.nickname} ({sid}) to game {client.gameCode}")
            
            # Send acknowledgment
            return {"status": "success", "message": "Successfully joined the game"}
            
        except Exception as e:
            logger.error(f"Error during join_game: {str(e)}")
            return {"status": "error", "message": str(e)}

    def setup(self):
        # Register event handlers
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('join_game', self.handle_join_game)
        
        return socketio.ASGIApp(self.sio)
