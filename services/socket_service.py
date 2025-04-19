import socketio
import time
import logging
import asyncio
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
        self.socket_id_map = {}  # 이전 소켓 ID와 새로운 소켓 ID 매핑
        # Need to have access to game_service
        self.game_service = None

    def _validate_position(self, position: str, game_code: str) -> bool:
        """Validate position against game settings"""
        if position == 'spectator':
            return True
            
        if not self.game_service or not hasattr(self.game_service, 'game_settings'):
            return False
            
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
            client.get('position') == position and client.get('gameCode') == game_code
            for client in self.clients.values()
        )

    def _is_clients_turn(self, client: dict, phase: int, player_type: str) -> bool:
        """Check if it's the client's turn based on phase and position"""
        if player_type == "single":
            return True

        # Get team and position from client position
        position = client.get('position')
        if position == "spectator":
            return False

        team = position[:-1]  # 'blue' or 'red'
        position_num = int(position[-1:])  # 1-5

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

    def _is_host(self, client: dict) -> bool:
        """Check if client is the host"""
        # 클라이언트 객체에 저장된 isHost 값을 반환
        return client.get('isHost', False)

    def _are_all_players_ready(self, game_code: str, player_type: str) -> bool:
        """Check if all required positions are filled and ready"""
        game_clients = [
            client for client in self.clients.values()
            if client.get('gameCode') == game_code and client.get('position') != 'spectator'
        ]

        if player_type == "1v1":
            # Need exactly one blue and one red player
            blue_ready = any(c.get('position') == "blue1" and c.get('isReady') for c in game_clients)
            red_ready = any(c.get('position') == "red1" and c.get('isReady') for c in game_clients)
            return blue_ready and red_ready

        elif player_type == "5v5":
            # Need all 5 positions filled and ready for both teams
            blue_positions = set(f"blue{i}" for i in range(1, 6))
            red_positions = set(f"red{i}" for i in range(1, 6))
            
            filled_and_ready = set(
                client.get('position')
                for client in game_clients
                if client.get('isReady')
            )
            
            return (blue_positions.issubset(filled_and_ready) and 
                   red_positions.issubset(filled_and_ready))

        return True  # For 'single' mode

    def _can_confirm_selection(self, client: dict, phase: int, player_type: str) -> bool:
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

    async def handle_connect(self, sid, environ, auth):
        """클라이언트 연결 시 호출되는 핸들러"""
        try:
            # 클라이언트 정보 저장
            self.clients[sid] = {
                'sid': sid,
                'socketId': auth.get('socketId') if auth else None,
                'gameCode': None,
                'nickname': None,
                'position': None,
                'isHost': False,
                'isReady': False,
                'champion': None,
                'isConfirmed': False
            }
            print(f"Client connected: {sid}")
            
            # 연결 성공 이벤트 전송
            await self.sio.emit('connection_success', {'sid': sid}, room=sid)
            
            return True
        except Exception as e:
            print(f"Error in handle_connect: {e}")
            return False

    async def handle_disconnect(self, sid: str, namespace: str = None):
        """클라이언트 연결 해제 시 호출되는 핸들러"""
        try:
            if sid in self.clients:
                client = self.clients[sid]
                # 게임 방에서 나가기
                if client.get('gameCode'):
                    await self.sio.leave_room(sid, client['gameCode'])
                    # 다른 클라이언트들에게 알림
                    await self.sio.emit('client_left', {
                        'nickname': client.get('nickname', 'Unknown'),
                        'position': client.get('position', 'spectator')
                    }, room=client['gameCode'])
                # 클라이언트 정보 삭제
                del self.clients[sid]
                print(f"Client disconnected: {sid}")
        except Exception as e:
            print(f"Error in handle_disconnect: {e}")

    async def handle_join_game(self, sid: str, data: dict):
        """게임 참가 요청 처리"""
        try:
            game_code = data.get('gameCode')
            nickname = data.get('nickname')
            position = data.get('position', 'spectator')
            socket_id = data.get('socketId')

            if not game_code or not nickname:
                return {"status": "error", "message": "게임 코드와 닉네임은 필수입니다."}

            # 게임에 참가한 플레이어가 있는지 확인
            existing_clients = [
                c for c in self.clients.values()
                if c.get('gameCode') == game_code
            ]
            
            # 첫 번째 참가자인 경우 호스트로 설정
            is_host = len(existing_clients) == 0
            
            # 클라이언트 정보 업데이트
            self.clients[sid] = {
                'sid': sid,
                'socketId': socket_id,
                'gameCode': game_code,
                'nickname': nickname,
                'position': position,
                'isHost': is_host,
                'isReady': False,
                'champion': None,
                'isConfirmed': False
            }

            # 게임 방에 참가
            await self.sio.enter_room(sid, game_code)

            # 다른 클라이언트들에게 알림
            await self.sio.emit('client_joined', {
                'nickname': nickname,
                'position': position,
                'isHost': is_host
            }, room=game_code)

            print(f"Client joined game: {nickname} ({sid}), isHost: {is_host}")
            return {
                "status": "success",
                "data": {
                    "socket_id": sid,
                    "position": position,
                    "isHost": is_host,
                    "clientId": sid
                }
            }
        except Exception as e:
            print(f"Error in handle_join_game: {e}")
            return {"status": "error", "message": "게임 참가에 실패했습니다."}

    async def handle_position_change(self, sid: str, data: dict):
        """Handle client position change request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            new_position = data.get('position')
            if not new_position:
                return {"status": "error", "message": "포지션이 지정되지 않았습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Validate new position
            if not self._validate_position(new_position, game_code):
                return {"status": "error", "message": "유효하지 않은 포지션입니다."}

            # Check if position is available
            if not self._is_position_available(new_position, game_code):
                return {"status": "error", "message": "이미 사용 중인 포지션입니다."}

            # Store previous position for notification
            old_position = client.get('position')

            # Update client position
            client['position'] = new_position
            self.clients[sid] = client

            # Broadcast position change to all clients in the game
            await self.sio.emit('position_changed', {
                'nickname': client.get('nickname'),
                'oldPosition': old_position,
                'newPosition': new_position
            }, room=game_code)

            print(f"Client {client.get('nickname')} changed position from {old_position} to {new_position}")
            return {"status": "success", "message": "포지션이 성공적으로 변경되었습니다."}

        except Exception as e:
            print(f"Error during position change: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_ready_state(self, sid: str, data: dict):
        """Handle client ready state change request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            is_ready = data.get('isReady', False)

            # Update client ready state
            client['isReady'] = is_ready
            self.clients[sid] = client

            # Broadcast ready state change to all clients in the game
            await self.sio.emit('ready_state_changed', {
                'nickname': client.get('nickname'),
                'position': client.get('position'),
                'isReady': is_ready
            }, room=client.get('gameCode'))

            print(f"Client {client.get('nickname')} ready state changed to: {is_ready}")
            return {"status": "success", "message": "준비 상태가 성공적으로 업데이트되었습니다."}

        except Exception as e:
            print(f"Error during ready state change: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_champion_select(self, sid: str, data: dict):
        """Handle champion selection request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            champion = data.get('champion')
            if not champion:
                return {"status": "error", "message": "챔피언이 지정되지 않았습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}
                
            # Validate phase is between 1 and 20
            if game_status.phase < 1 or game_status.phase > 20:
                return {"status": "error", "message": "현재 페이즈에서는 챔피언 선택이 불가능합니다."}

            # Check if it's client's turn
            if not self._is_clients_turn(client, game_status.phase, game_settings.playerType):
                return {"status": "error", "message": "당신의 차례가 아닙니다."}

            # Update phase data with selected champion
            game_status.phaseData[game_status.phase] = champion
            game_status.lastUpdatedAt = self._get_timestamp()

            # Save updated status
            self.game_service.game_status[game_code] = game_status

            # Broadcast champion selection to all clients in the game
            await self.sio.emit('champion_selected', {
                'nickname': client.get('nickname'),
                'position': client.get('position'),
                'champion': champion,
                'phase': game_status.phase
            }, room=game_code)

            print(f"Champion selected: {champion} by {client.get('nickname')} in phase {game_status.phase}")
            return {"status": "success", "message": "챔피언이 성공적으로 선택되었습니다."}

        except Exception as e:
            print(f"Error during champion selection: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_confirm_selection(self, sid: str, data: dict):
        """Handle champion selection confirmation and phase progression"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}

            current_phase = game_status.phase

            # Check if current phase is valid for progression
            if current_phase >= 21:
                return {"status": "error", "message": "이미 밴픽이 완료되었습니다."}

            # Check if it's client's turn to confirm
            if not self._can_confirm_selection(client, current_phase, game_settings.playerType):
                return {"status": "error", "message": "당신의 차례가 아닙니다."}

            # Define ban phases
            BAN_PHASES = list(range(1, 7)) + list(range(13, 17))  # Phases 1-6 and 13-16 are ban phases
            
            # Check if a champion is selected in current phase (only required for pick phases)
            if not game_status.phaseData[current_phase] and current_phase not in BAN_PHASES:
                return {"status": "error", "message": "현재 페이즈에서 선택된 챔피언이 없습니다."}

            # Update phase
            game_status.phase = current_phase + 1
            game_status.lastUpdatedAt = self._get_timestamp()

            # Save updated status
            self.game_service.game_status[game_code] = game_status

            # Broadcast phase progression to all clients in the game
            await self.sio.emit('phase_progressed', {
                'gameCode': game_code,
                'confirmedBy': client.get('nickname'),
                'fromPhase': current_phase,
                'toPhase': game_status.phase,
                'confirmedChampion': game_status.phaseData[current_phase],
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            print(f"Phase progressed from {current_phase} to {game_status.phase} by {client.get('nickname')}")
            return {"status": "success", "message": "페이즈가 성공적으로 진행되었습니다."}

        except Exception as e:
            print(f"Error during phase progression: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_start_draft(self, sid: str, data: dict):
        """Handle draft start request"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Check if client is host
            if not self._is_host(client):
                return {"status": "error", "message": "호스트만 게임을 시작할 수 있습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}

            # Check if game is in initial phase
            if game_status.phase != 0:
                return {"status": "error", "message": "이미 게임이 시작되었습니다."}

            # For non-single modes, check if all players are ready
            if game_settings.playerType != "single":
                if not self._are_all_players_ready(game_code, game_settings.playerType):
                    return {"status": "error", "message": "모든 플레이어가 준비 상태여야 합니다."}

            # Update game status to start draft
            game_status.phase = 1
            game_status.lastUpdatedAt = self._get_timestamp()
            self.game_service.game_status[game_code] = game_status

            # Broadcast draft start to all clients in the game
            await self.sio.emit('draft_started', {
                'gameCode': game_code,
                'startedBy': client.get('nickname'),
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            print(f"Draft started in game {game_code} by {client.get('nickname')}")
            return {"status": "success", "message": "게임이 성공적으로 시작되었습니다."}

        except Exception as e:
            print(f"Error during draft start: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_confirm_result(self, sid: str, data: dict):
        """Handle game result confirmation by the host"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Check if client is host
            if not self._is_host(client):
                return {"status": "error", "message": "호스트만 게임 결과를 확정할 수 있습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}

            # Check if game phase is 21 (game end)
            if game_status.phase != 21:
                return {"status": "error", "message": "게임이 완료 단계가 아닙니다."}

            winner = data.get('winner')
            if winner not in ['blue', 'red']:
                return {"status": "error", "message": "승자 값이 잘못되었습니다. 'blue' 또는 'red'여야 합니다."}

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
                if client_obj.get('gameCode') == game_code and client_obj.get('position') != 'spectator':
                    client_obj['isReady'] = False
                    self.clients[client_sid] = client_obj

            # Save updated status
            self.game_service.game_status[game_code] = game_status
            self.game_service.game_results[game_code] = game_result

            # Broadcast game result confirmation to all clients in the game
            await self.sio.emit('game_result_confirmed', {
                'gameCode': game_code,
                'confirmedBy': client.get('nickname'),
                'winner': winner,
                'blueScore': game_result.blueScore,
                'redScore': game_result.redScore,
                'nextSetNumber': game_status.setNumber,
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)

            print(f"Game result confirmed in {game_code}: {winner} wins. Moving to set {game_status.setNumber}")
            return {"status": "success", "message": "게임 결과가 성공적으로 확정되었습니다."}

        except Exception as e:
            print(f"Error during game result confirmation: {e}")
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
