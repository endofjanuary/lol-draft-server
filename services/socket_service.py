import socketio
import time
import logging
from typing import Dict, List
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

    def _validate_position(self, position: str, game_code: str) -> bool:
        """Validate position against game settings"""
        if position == 'spectator':
            return True
            
        game_settings = self.game_service.game_settings.get(game_code)
        if not game_settings:
            return False

        valid_positions = {
            'single': ['all'],
            '1v1': ['blue1', 'red1'],
            '5v5': [f'blue{i}' for i in range(1, 6)] + [f'red{i}' for i in range(1, 6)]
        }
        
        return position in valid_positions.get(game_settings.playerType, [])

    def _is_position_available(self, position: str, game_code: str) -> bool:
        """Check if position is already taken"""
        if position == 'spectator':
            return True
            
        return not any(
            client.position == position and client.gameCode == game_code
            for client in self.clients.values()
        )

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
            game_code = data['gameCode']
            position = data.get('position', 'spectator')

            # Validate position if specified
            if position != 'spectator' and not self._validate_position(position, game_code):
                return {"status": "error", "message": "Invalid position"}

            if not self._is_position_available(position, game_code):
                return {"status": "error", "message": "Position already taken"}

            # Create client object
            client = Client(
                socketId=sid,
                gameCode=game_code,
                position=position,
                joinedAt=int(time.time() * 1000000),
                nickname=data['nickname']
            )
            
            # Store client and join room
            self.clients[sid] = client
            await self.sio.enter_room(sid, game_code)
            
            # Broadcast join event
            await self.sio.emit('client_joined', {
                'nickname': client.nickname,
                'position': position
            }, room=game_code)
            
            logger.info(f"Client joined: {client.nickname} ({sid}) to game {client.gameCode}")
            return {"status": "success", "message": "Successfully joined the game"}
            
        except Exception as e:
            logger.error(f"Error during join_game: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_position_change(self, sid: str, data: dict):
        """Handle client position change request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            new_position = data.get('position')
            if not new_position:
                return {"status": "error", "message": "Position not specified"}

            client = self.clients[sid]
            game_code = client.gameCode

            # Validate new position
            if not self._validate_position(new_position, game_code):
                return {"status": "error", "message": "Invalid position"}

            # Check if position is available
            if not self._is_position_available(new_position, game_code):
                return {"status": "error", "message": "Position already taken"}

            # Store previous position for notification
            old_position = client.position

            # Update client position
            client.position = new_position
            self.clients[sid] = client

            # Broadcast position change to all clients in the game
            await self.sio.emit('position_changed', {
                'nickname': client.nickname,
                'oldPosition': old_position,
                'newPosition': new_position
            }, room=game_code)

            logger.info(f"Client {client.nickname} changed position from {old_position} to {new_position}")
            return {"status": "success", "message": "Position changed successfully"}

        except Exception as e:
            logger.error(f"Error during position change: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_ready_state(self, sid: str, data: dict):
        """Handle client ready state change request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            client = self.clients[sid]
            is_ready = data.get('isReady', False)

            # Update client ready state
            client.isReady = is_ready
            self.clients[sid] = client

            # Broadcast ready state change to all clients in the game
            await self.sio.emit('ready_state_changed', {
                'nickname': client.nickname,
                'position': client.position,
                'isReady': is_ready
            }, room=client.gameCode)

            logger.info(f"Client {client.nickname} ready state changed to: {is_ready}")
            return {"status": "success", "message": "Ready state updated successfully"}

        except Exception as e:
            logger.error(f"Error during ready state change: {str(e)}")
            return {"status": "error", "message": str(e)}

    def setup(self):
        # Register event handlers
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('join_game', self.handle_join_game)
        self.sio.on('change_position', self.handle_position_change)
        self.sio.on('change_ready_state', self.handle_ready_state)
        
        return socketio.ASGIApp(self.sio)
