import time
import secrets
from models import Game, GameSetting, GameStatus
from fastapi import Request

class GameService:
    def __init__(self):
        self.games = {}
        self.game_settings = {}
        self.game_status = {}
        self.socket_service = None  # SocketService 참조를 저장할 변수
    
    async def create_game(self, setting: GameSetting, request: Request = None) -> Game:
        """새로운 게임을 생성합니다."""
        try:
            # Generate unique game code
            while True:
                game_code = secrets.token_hex(4)
                if game_code not in self.games:
                    break
        
            current_time = int(time.time() * 1000000)
        
            # Extract additional data from request body
            game_name = "New Game"
            blue_team_name = "Blue"
            red_team_name = "Red"
        
            if request:
                try:
                    raw_body = await request.json()
                    if "gameName" in raw_body:
                        game_name = raw_body["gameName"]
                    if "teamNames" in raw_body and isinstance(raw_body["teamNames"], dict):
                        team_names = raw_body["teamNames"]
                        if "blue" in team_names:
                            blue_team_name = team_names["blue"]
                        if "red" in team_names:
                            red_team_name = team_names["red"]
                except Exception as e:
                    print(f"Error extracting additional game data: {e}")
        
            # Initialize game with game name
            game = Game(
                gameCode=game_code,
                createdAt=current_time,
                gameName=game_name
            )
        
            # Initialize game status with team names
            status = GameStatus(
                lastUpdatedAt=current_time,
                phaseData=[""] * 22,
                blueTeamName=blue_team_name,
                redTeamName=red_team_name,
                phase=0,  # 초기 페이즈는 0
                setNumber=1,  # 초기 세트 번호는 1
                blueScore=0,  # 초기 점수는 0
                redScore=0
            )
        
            # Store in memory
            self.games[game_code] = game
            self.game_settings[game_code] = setting
            self.game_status[game_code] = status
        
            print(f"Game created: {game_code}")
            return game
        except Exception as e:
            print(f"Error in create_game: {e}")
            raise

    def get_game_info(self, game_code: str):
        if game_code not in self.games:
            raise ValueError(f"Game not found: {game_code}")
            
        return {
            "game": self.games[game_code],
            "settings": self.game_settings[game_code],
            "status": self.game_status[game_code]
        }

    def get_game(self, game_code: str) -> dict:
        """게임 정보를 반환합니다."""
        try:
            # 게임 설정과 상태를 가져옵니다
            game_settings = self.game_settings.get(game_code)
            game_status = self.game_status.get(game_code)
            
            if not game_settings or not game_status:
                raise ValueError("게임을 찾을 수 없습니다.")
            
            # 게임에 참가한 클라이언트 정보를 가져옵니다
            clients = []
            if self.socket_service and hasattr(self.socket_service, 'clients'):
                for client in self.socket_service.clients.values():
                    if client.get('gameCode') == game_code:
                        # 클라이언트 정보를 그대로 가져와서 필요한 정보만 추출
                        clients.append({
                            'nickname': client.get('nickname'),
                            'position': client.get('position'),
                            'isHost': client.get('isHost', False),  # 저장된 방장 정보 사용
                            'isReady': client.get('isReady', False),
                            'champion': client.get('champion'),
                            'isConfirmed': client.get('isConfirmed', False),
                            'clientId': client.get('sid')
                        })
            
            # 게임 정보를 구성합니다
            game_info = {
                'code': game_code,
                'settings': {
                    'playerType': game_settings.playerType,
                    'matchFormat': game_settings.matchFormat,
                    'version': game_settings.version,  # 버전 정보 추가
                    'timeLimit': game_settings.timeLimit,
                    'globalBans': game_settings.globalBans,
                    'bannerImage': game_settings.bannerImage if hasattr(game_settings, 'bannerImage') else None,
                },
                'status': {
                    'phase': game_status.phase,
                    'phaseData': game_status.phaseData,
                    'setNumber': game_status.setNumber,
                    'lastUpdatedAt': game_status.lastUpdatedAt,
                    'blueTeamName': game_status.blueTeamName,
                    'redTeamName': game_status.redTeamName,
                },
                'clients': clients,
                'blueScore': game_status.blueScore,
                'redScore': game_status.redScore
            }
            
            print(f"Game info for {game_code}: {game_info}")
            return game_info
        except Exception as e:
            print(f"Error in get_game: {e}")
            raise
