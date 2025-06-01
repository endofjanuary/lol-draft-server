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
            '1v1': ['team1', 'team2'],  # 변경: blue1, red1 → team1, team2
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

        # position은 이제 'team1' 또는 'team2'
        team = position  # 'team1' 또는 'team2'
        
        # 게임 상태 정보 가져오기
        game_code = client.get('gameCode')
        if not game_code or not self.game_service:
            return False
            
        game_status = self.game_service.game_status.get(game_code)
        if not game_status:
            return False

        # Phase ranges
        BAN_PHASE_1 = range(1, 7)    # 1-6
        PICK_PHASE_1 = range(7, 13)  # 7-12
        BAN_PHASE_2 = range(13, 17)  # 13-16
        PICK_PHASE_2 = range(17, 21) # 17-20

        # Ban phases - only team captain can ban (1v1에서는 팀 대표자)
        if phase in BAN_PHASE_1 or phase in BAN_PHASE_2:
            # 1v1에서는 각 팀의 대표자가 밴을 담당
            pass

        # 현재 어느 팀이 blue/red 진영인지 확인
        team1_side = game_status.team1Side  # 'blue' or 'red'
        team2_side = game_status.team2Side  # 'red' or 'blue'
        
        # Phase mapping - 블루 진영이 먼저 시작하는 페이즈들
        blue_turn_phases = {1, 3, 5, 7, 10, 11, 14, 16, 18, 19}
        red_turn_phases = {2, 4, 6, 8, 9, 12, 13, 15, 17, 20}
        
        if phase in blue_turn_phases:
            # Blue 진영의 차례
            required_team = "team1" if team1_side == "blue" else "team2"
        elif phase in red_turn_phases:
            # Red 진영의 차례  
            required_team = "team1" if team1_side == "red" else "team2"
        else:
            return False
            
        return team == required_team

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
            # Need exactly one team1 and one team2 player
            team1_ready = any(c.get('position') == "team1" and c.get('isReady') for c in game_clients)
            team2_ready = any(c.get('position') == "team2" and c.get('isReady') for c in game_clients)
            return team1_ready and team2_ready

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

    def _is_final_set(self, game_result, match_format: str) -> bool:
        """마지막 세트인지 확인"""
        if match_format == "bo1":
            return True
        elif match_format == "bo3":
            return game_result.team1Score >= 2 or game_result.team2Score >= 2
        elif match_format == "bo5":
            return game_result.team1Score >= 3 or game_result.team2Score >= 3
        return False

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

            # 첫 번째 플레이어는 자동으로 호스트가 됨
            is_host = len(existing_clients) == 0

            # 클라이언트 정보 업데이트
            self.clients[sid].update({
                'gameCode': game_code,
                'nickname': nickname,
                'position': position,
                'isHost': is_host,
                'joinedAt': self._get_timestamp()
            })

            # 게임 방에 참가
            await self.sio.enter_room(sid, game_code)

            # 다른 클라이언트들에게 알림
            await self.sio.emit('client_joined', {
                'nickname': nickname,
                'position': position,
                'isHost': is_host,
                'clientId': sid
            }, room=game_code)

            print(f"{nickname} joined game {game_code} at position {position}")
            return {
                "status": "success", 
                "message": "게임에 성공적으로 참가했습니다.",
                "data": {
                    "position": position,
                    "isHost": is_host,
                    "clientId": sid
                }
            }

        except Exception as e:
            print(f"Error in handle_join_game: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_position_change(self, sid: str, data: dict):
        """포지션 변경 요청 처리"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')
            new_position = data.get('position')

            if not game_code or not new_position:
                return {"status": "error", "message": "게임 코드 또는 포지션이 없습니다."}

            # 유효한 포지션인지 확인
            if not self._validate_position(new_position, game_code):
                return {"status": "error", "message": "유효하지 않은 포지션입니다."}

            # 포지션이 사용 가능한지 확인 (본인 제외)
            if new_position != "spectator":
                position_taken = any(
                    c.get('position') == new_position and c.get('gameCode') == game_code and c.get('sid') != sid
                    for c in self.clients.values()
                )
                if position_taken:
                    return {"status": "error", "message": "이미 사용 중인 포지션입니다."}

            old_position = client.get('position')
            
            # 클라이언트 포지션 업데이트
            self.clients[sid]['position'] = new_position

            # 다른 클라이언트들에게 알림
            await self.sio.emit('position_changed', {
                'nickname': client.get('nickname'),
                'oldPosition': old_position,
                'newPosition': new_position
            }, room=game_code)

            print(f"{client.get('nickname')} changed position from {old_position} to {new_position}")
            return {"status": "success", "message": "포지션이 성공적으로 변경되었습니다."}

        except Exception as e:
            print(f"Error in handle_position_change: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_ready_state(self, sid: str, data: dict):
        """준비 상태 변경 요청 처리"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')
            is_ready = data.get('isReady', False)

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # 준비 상태 업데이트
            self.clients[sid]['isReady'] = is_ready

            # 다른 클라이언트들에게 알림
            await self.sio.emit('ready_state_changed', {
                'nickname': client.get('nickname'),
                'position': client.get('position'),
                'isReady': is_ready
            }, room=game_code)

            print(f"{client.get('nickname')} ready state: {is_ready}")
            return {"status": "success", "message": "준비 상태가 성공적으로 변경되었습니다."}

        except Exception as e:
            print(f"Error in handle_ready_state: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_champion_select(self, sid: str, data: dict):
        """챔피언 선택 처리"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')
            champion = data.get('champion')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            if not champion:
                return {"status": "error", "message": "챔피언이 선택되지 않았습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}

            current_phase = game_status.phase

            # Check if it's client's turn
            if not self._is_clients_turn(client, current_phase, game_settings.playerType):
                return {"status": "error", "message": "당신의 차례가 아닙니다."}

            # Update phase data
            if current_phase < len(game_status.phaseData):
                game_status.phaseData[current_phase] = champion
                game_status.lastUpdatedAt = self._get_timestamp()
                
                # Save updated status
                self.game_service.game_status[game_code] = game_status

                # Broadcast champion selection to all clients in the game
                await self.sio.emit('champion_selected', {
                    'gameCode': game_code,
                    'selectedBy': client.get('nickname'),
                    'champion': champion,
                    'phase': current_phase,
                    'timestamp': game_status.lastUpdatedAt
                }, room=game_code)

                print(f"Champion {champion} selected by {client.get('nickname')} in phase {current_phase}")
                return {"status": "success", "message": "챔피언이 성공적으로 선택되었습니다."}
            else:
                return {"status": "error", "message": "유효하지 않은 페이즈입니다."}

        except Exception as e:
            print(f"Error during champion selection: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_confirm_selection(self, sid: str, data: dict):
        """선택 확정 처리"""
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
            if game_code not in self.game_service.game_results:
                from models import GameResult
                self.game_service.game_results[game_code] = GameResult()
            
            # Update score based on current sides
            game_result = self.game_service.game_results[game_code]
            blue_team_info = self.game_service.get_current_blue_team_info(game_code)
            
            if winner == 'blue':
                if blue_team_info["team"] == "team1":
                    game_result.team1Score += 1
                else:
                    game_result.team2Score += 1
            else:  # winner == 'red'
                if blue_team_info["team"] == "team1":
                    game_result.team2Score += 1
                else:
                    game_result.team1Score += 1
                
            # Store the phase data for this set in results
            while len(game_result.results) < game_status.setNumber:
                game_result.results.append([])
            
            game_result.results[game_status.setNumber - 1] = game_status.phaseData

            # Check if this is the final set
            if not self._is_final_set(game_result, game_settings.matchFormat):
                # Not final set - go to side choice phase
                game_status.phase = 22  # 새로운 진영 선택 페이즈
                
                # 패배한 팀 결정 (현재 진영 기준)
                losing_side = "red" if winner == "blue" else "blue"
                
                # Save updated status
                game_status.lastUpdatedAt = self._get_timestamp()
                self.game_service.game_status[game_code] = game_status
                self.game_service.game_results[game_code] = game_result
                
                await self.sio.emit('side_choice_phase', {
                    'gameCode': game_code,
                    'losingSide': losing_side,
                    'winner': winner,
                    'currentScores': {
                        'team1': game_result.team1Score,
                        'team2': game_result.team2Score
                    },
                    'timestamp': game_status.lastUpdatedAt
                }, room=game_code)
            else:
                # Final set - match finished
                game_status.phase = 23  # 매치 완료 페이즈
                game_status.lastUpdatedAt = self._get_timestamp()
                self.game_service.game_status[game_code] = game_status
                self.game_service.game_results[game_code] = game_result
                
                await self.sio.emit('match_finished', {
                    'gameCode': game_code,
                    'finalWinner': winner,
                    'finalScores': {
                        'team1': game_result.team1Score,
                        'team2': game_result.team2Score
                    },
                    'timestamp': game_status.lastUpdatedAt
                }, room=game_code)

            print(f"Game result confirmed in {game_code}: {winner} wins. Scores: Team1={game_result.team1Score}, Team2={game_result.team2Score}")
            return {"status": "success", "message": "게임 결과가 성공적으로 확정되었습니다."}

        except Exception as e:
            print(f"Error during game result confirmation: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_side_choice(self, sid: str, data: dict):
        """진영 선택 처리"""
        try:
            if sid not in self.clients:
                return {"status": "error", "message": "클라이언트를 찾을 수 없습니다."}

            client = self.clients[sid]
            game_code = client.get('gameCode')

            if not game_code:
                return {"status": "error", "message": "게임 코드가 없습니다."}

            # Check if client is host
            if not self._is_host(client):
                return {"status": "error", "message": "호스트만 진영을 선택할 수 있습니다."}

            # Get game settings and status
            game_settings = self.game_service.game_settings.get(game_code)
            game_status = self.game_service.game_status.get(game_code)
            
            if not game_settings or not game_status:
                return {"status": "error", "message": "게임을 찾을 수 없습니다."}

            # Check if game is in side choice phase
            if game_status.phase != 22:
                return {"status": "error", "message": "진영 선택 단계가 아닙니다."}

            choice = data.get('choice')  # 'keep' 또는 'swap'
            if choice not in ['keep', 'swap']:
                return {"status": "error", "message": "유효하지 않은 선택입니다."}
            
            # Handle side choice
            await self.game_service.handle_side_choice(game_code, choice)
            
            # Move to next set
            game_status.setNumber += 1
            game_status.phase = 0  # Reset to preparation phase
            game_status.phaseData = [""] * 22
            game_status.lastUpdatedAt = self._get_timestamp()
            
            # Reset ready state for all players in this game
            for client_sid, client_obj in self.clients.items():
                if client_obj.get('gameCode') == game_code and client_obj.get('position') != 'spectator':
                    client_obj['isReady'] = False
                    self.clients[client_sid] = client_obj

            # Save updated status
            self.game_service.game_status[game_code] = game_status
            
            await self.sio.emit('next_set_started', {
                'gameCode': game_code,
                'setNumber': game_status.setNumber,
                'sideChoice': choice,
                'currentSides': {
                    'team1': game_status.team1Side,
                    'team2': game_status.team2Side
                },
                'timestamp': game_status.lastUpdatedAt
            }, room=game_code)
            
            print(f"Next set started in {game_code}: Set {game_status.setNumber}, Side choice: {choice}")
            return {"status": "success", "message": "다음 세트가 성공적으로 시작되었습니다."}
            
        except Exception as e:
            print(f"Error during side choice: {e}")
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
        self.sio.on('confirm_result', self.handle_confirm_result)
        self.sio.on('choose_side', self.handle_side_choice)  # Add new handler
        
        return socketio.ASGIApp(self.sio)
