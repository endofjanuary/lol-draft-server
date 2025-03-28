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
        # Need to have access to game_service
        self.game_service = None

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

    def _is_clients_turn(self, client: Client, phase: int, player_type: str) -> bool:
        """Check if it's the client's turn based on phase and position"""
        if player_type == "single":
            return True

        # Get team and position number from client position
        if client.position == "spectator":
            return False

        team = client.position[:-1]  # 'blue' or 'red'
        position_num = int(client.position[-1:])  # 1-5

        # Phase ranges
        BAN_PHASE_1 = range(1, 7)    # 1-6
        PICK_PHASE_1 = range(7, 13)  # 7-12
        BAN_PHASE_2 = range(13, 17)  # 13-16
        PICK_PHASE_2 = range(17, 21) # 17-20

        # Ban phases - only team captain (position 1) can ban
        if phase in BAN_PHASE_1 or phase in BAN_PHASE_2:
            if position_num != 1:
                return False

        # Map phase to team and position
        phase_map = {
            # First ban phase (1-6)
            1: ("blue", 1), 2: ("red", 1), 3: ("blue", 1),
            4: ("red", 1), 5: ("blue", 1), 6: ("red", 1),
            # First pick phase (7-12)
            7: ("blue", 1), 8: ("red", 1), 9: ("red", 2),
            10: ("blue", 2), 11: ("blue", 3), 12: ("red", 3),
            # Second ban phase (13-16)
            13: ("red", 1), 14: ("blue", 1), 15: ("red", 1), 16: ("blue", 1),
            # Second pick phase (17-20)
            17: ("red", 4), 18: ("blue", 4), 19: ("blue", 5), 20: ("red", 5)
        }

        if phase not in phase_map:
            return False

        required_team, required_pos = phase_map[phase]
        
        if player_type == "1v1":
            # In 1v1, any position can act when it's their team's turn
            return team == required_team
        else:  # 5v5
            return team == required_team and position_num == required_pos

    def _is_host(self, client: Client) -> bool:
        """Check if client is the host (earliest joinedAt in the game)"""
        game_clients = [
            c for c in self.clients.values()
            if c.gameCode == client.gameCode
        ]
        if not game_clients:
            return False
        return client.joinedAt == min(c.joinedAt for c in game_clients)

    def _are_all_players_ready(self, game_code: str, player_type: str) -> bool:
        """Check if all required positions are filled and ready"""
        game_clients = [
            client for client in self.clients.values()
            if client.gameCode == game_code and client.position != 'spectator'
        ]

        if player_type == "1v1":
            # Need exactly one blue and one red player
            blue_ready = any(c.position == "blue1" and c.isReady for c in game_clients)
            red_ready = any(c.position == "red1" and c.isReady for c in game_clients)
            return blue_ready and red_ready

        elif player_type == "5v5":
            # Need all 5 positions filled and ready for both teams
            blue_positions = set(f"blue{i}" for i in range(1, 6))
            red_positions = set(f"red{i}" for i in range(1, 6))
            
            filled_and_ready = set(
                client.position
                for client in game_clients
                if client.isReady
            )
            
            return (blue_positions.issubset(filled_and_ready) and 
                   red_positions.issubset(filled_and_ready))

        return True  # For 'single' mode

    def _can_confirm_selection(self, client: Client, phase: int, player_type: str) -> bool:
        """Check if client can confirm selection in current phase"""
        # Re-use existing turn validation logic
        return self._is_clients_turn(client, phase, player_type)

    def _get_timestamp(self) -> int:
        """Generate a reliable timestamp in microseconds"""
        try:
            return int(time.time() * 1000000)
        except (ValueError, TypeError) as e:
            logger.error(f"Error generating timestamp: {e}")
            # Fallback to a simpler timestamp format (milliseconds)
            return int(time.time() * 1000)

    async def handle_connect(self, sid: str, environ):
        logger.debug(f"Client attempting to connect: {sid}")
        await self.sio.emit('connection_success', {'sid': sid}, room=sid)
        logger.info(f"Client connected: {sid}")

    async def handle_disconnect(self, sid: str):
        if sid in self.clients:
            client = self.clients[sid]
            # Broadcast client_left event to the game room
            await self.sio.emit('client_left', {
                'nickname': client.nickname,
                'position': client.position
            }, room=client.gameCode)
            
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
                joinedAt=self._get_timestamp(),
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

    async def handle_champion_select(self, sid: str, data: dict):
        """Handle champion selection request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            champion = data.get('champion')
            if not champion:
                return {"status": "error", "message": "Champion not specified"}

            client = self.clients[sid]
            game_code = client.gameCode

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "Game not found"}
                
            # Validate phase is between 1 and 20
            if game_status.phase < 1 or game_status.phase > 20:
                return {"status": "error", "message": "Champion selection not allowed in current phase"}

            # Check if it's client's turn
            if not self._is_clients_turn(client, game_status.phase, game_settings.playerType):
                return {"status": "error", "message": "Not your turn"}

            # Update phase data with selected champion
            game_status.phaseData[game_status.phase] = champion
            game_status.lastUpdatedAt = self._get_timestamp()

            # Save updated status
            self.game_service.game_status[game_code] = game_status

            # Broadcast champion selection to all clients in the game
            await self.sio.emit('champion_selected', {
                'nickname': client.nickname,
                'position': client.position,
                'champion': champion,
                'phase': game_status.phase
            }, room=game_code)

            logger.info(f"Champion selected: {champion} by {client.nickname} in phase {game_status.phase}")
            return {"status": "success", "message": "Champion selected successfully"}

        except Exception as e:
            logger.error(f"Error during champion selection: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_confirm_selection(self, sid: str, data: dict):
        """Handle champion selection confirmation and phase progression"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            client = self.clients[sid]
            game_code = client.gameCode

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "Game not found"}

            current_phase = game_status.phase

            # Check if current phase is valid for progression
            if current_phase >= 21:
                return {"status": "error", "message": "Draft is already complete"}

            # Check if it's client's turn to confirm
            if not self._can_confirm_selection(client, current_phase, game_settings.playerType):
                return {"status": "error", "message": "Not your turn to confirm"}

            # Define ban phases
            BAN_PHASES = list(range(1, 7)) + list(range(13, 17))  # Phases 1-6 and 13-16 are ban phases
            
            # Check if a champion is selected in current phase (only required for pick phases)
            if not game_status.phaseData[current_phase] and current_phase not in BAN_PHASES:
                return {"status": "error", "message": "No champion selected for current phase"}

            # Update phase
            game_status.phase = current_phase + 1
            game_status.lastUpdatedAt = self._get_timestamp()

            # Save updated status
            self.game_service.game_status[game_code] = game_status

            # Broadcast phase progression to all clients in the game
            await self.sio.emit('phase_progressed', {
                'gameCode': game_code,
                'confirmedBy': client.nickname,
                'fromPhase': current_phase,
                'toPhase': game_status.phase,
                'confirmedChampion': game_status.phaseData[current_phase],
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            logger.info(f"Phase progressed from {current_phase} to {game_status.phase} by {client.nickname}")
            return {"status": "success", "message": "Phase progressed successfully"}

        except Exception as e:
            logger.error(f"Error during phase progression: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_start_draft(self, sid: str, data: dict):
        """Handle draft start request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            client = self.clients[sid]
            game_code = client.gameCode

            # Check if client is host
            if not self._is_host(client):
                return {"status": "error", "message": "Only the host can start the draft"}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "Game not found"}

            # Check if game is in initial phase
            if game_status.phase != 0:
                return {"status": "error", "message": "Draft has already started"}

            # For non-single modes, check if all players are ready
            if game_settings.playerType != "single":
                if not self._are_all_players_ready(game_code, game_settings.playerType):
                    return {"status": "error", "message": "All players must be ready to start"}

            # Update game status to start draft
            game_status.phase = 1
            game_status.lastUpdatedAt = self._get_timestamp()
            self.game_service.game_status[game_code] = game_status

            # Broadcast draft start to all clients in the game
            await self.sio.emit('draft_started', {
                'gameCode': game_code,
                'startedBy': client.nickname,
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            logger.info(f"Draft started in game {game_code} by {client.nickname}")
            return {"status": "success", "message": "Draft started successfully"}

        except Exception as e:
            logger.error(f"Error during draft start: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_confirm_result(self, sid: str, data: dict):
        """Handle game result confirmation by the host"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "Client not found"}

            client = self.clients[sid]
            game_code = client.gameCode

            # Check if client is host
            if not self._is_host(client):
                return {"status": "error", "message": "Only the host can confirm game result"}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "Game not found"}

            # Check if game phase is 21 (game end)
            if game_status.phase != 21:
                return {"status": "error", "message": "Game is not in completion phase"}

            winner = data.get('winner')
            if winner not in ['blue', 'red']:
                return {"status": "error", "message": "Invalid winner value. Must be 'blue' or 'red'"}

            # Record the winner in phase data
            game_status.phaseData[21] = winner
            
            # Store current set result before resetting
            if 'game_results' not in self.game_service.__dict__:
                self.game_service.game_results = {}
                
            if game_code not in self.game_service.game_results:
                from models import GameResult
                self.game_service.game_results[game_code] = GameResult()
            
            # Update score
            game_result = self.game_service.game_results[game_code]
            if winner == 'blue':
                game_result.blueScore += 1
            else:
                game_result.redScore += 1
                
            # Store the phase data for this set in results
            while len(game_result.results) < game_status.setNumber:
                game_result.results.append([])
            
            game_result.results[game_status.setNumber - 1] = game_status.phaseData

            # Move to next set
            game_status.setNumber += 1
            game_status.phase = 0  # Reset to preparation phase
            game_status.lastUpdatedAt = self._get_timestamp()

            # Clear phase data for the new set
            game_status.phaseData = [""] * 22

            # Reset ready state for all players in this game
            for client_sid, client_obj in self.clients.items():
                if client_obj.gameCode == game_code and client_obj.position != 'spectator':
                    client_obj.isReady = False
                    self.clients[client_sid] = client_obj

            # Save updated status
            self.game_service.game_status[game_code] = game_status
            self.game_service.game_results[game_code] = game_result

            # Broadcast game result confirmation to all clients in the game
            await self.sio.emit('game_result_confirmed', {
                'gameCode': game_code,
                'confirmedBy': client.nickname,
                'winner': winner,
                'blueScore': game_result.blueScore,
                'redScore': game_result.redScore,
                'nextSetNumber': game_status.setNumber,
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            logger.info(f"Game result confirmed in {game_code}: {winner} wins. Moving to set {game_status.setNumber}")
            return {"status": "success", "message": "Game result confirmed successfully"}

        except Exception as e:
            logger.error(f"Error during game result confirmation: {str(e)}")
            return {"status": "error", "message": str(e)}

    def setup(self):
        # Register event handlers
        self.sio.on('connect', self.handle_connect)
        self.sio.on('disconnect', self.handle_disconnect)
        self.sio.on('join_game', self.handle_join_game)
        self.sio.on('change_position', self.handle_position_change)
        self.sio.on('change_ready_state', self.handle_ready_state)
        self.sio.on('select_champion', self.handle_champion_select)
        self.sio.on('confirm_selection', self.handle_confirm_selection)
        self.sio.on('start_draft', self.handle_start_draft)
        self.sio.on('confirm_result', self.handle_confirm_result)  # Add new handler
        
        return socketio.ASGIApp(self.sio)
