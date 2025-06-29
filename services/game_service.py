import time
import secrets
from models import Game, GameSetting, GameStatus
from fastapi import Request

class GameService:
    def __init__(self):
        self.games = {}
        self.game_settings = {}
        self.game_status = {}
        self.game_results = {}  # GameResult 저장용
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
            team1_name = "Team 1"
            team2_name = "Team 2"
        
            if request:
                try:
                    raw_body = await request.json()
                    if "gameName" in raw_body:
                        game_name = raw_body["gameName"]
                    if "teamNames" in raw_body and isinstance(raw_body["teamNames"], dict):
                        team_names = raw_body["teamNames"]
                        if "team1" in team_names:
                            team1_name = team_names["team1"]
                        elif "blue" in team_names:  # 하위 호환성
                            team1_name = team_names["blue"]
                        if "team2" in team_names:
                            team2_name = team_names["team2"]
                        elif "red" in team_names:  # 하위 호환성
                            team2_name = team_names["red"]
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
                team1Name=team1_name,
                team2Name=team2_name,
                phase=0,  # 초기 페이즈는 0
                setNumber=1,  # 초기 세트 번호는 1
                team1Side="blue",  # Team 1은 초기에 블루 진영
                team2Side="red"    # Team 2는 초기에 레드 진영
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

    async def handle_side_choice(self, game_code: str, choice: str):
        """진영 선택 처리"""
        if game_code not in self.game_status:
            raise ValueError("게임을 찾을 수 없습니다.")
        
        game_status = self.game_status[game_code]
        
        if choice == "swap":
            # 팀 진영 교체
            game_status.team1Side, game_status.team2Side = game_status.team2Side, game_status.team1Side
        
        # 선택 기록 저장
        if game_code in self.game_results:
            self.game_results[game_code].sideChoices.append(choice)
        
        return {"status": "success", "choice": choice}

    def get_current_blue_team_info(self, game_code: str):
        """현재 블루 진영에 있는 팀 정보 반환"""
        game_status = self.game_status.get(game_code)
        if not game_status:
            return None
        
        if game_status.team1Side == "blue":
            return {"name": game_status.team1Name, "team": "team1"}
        else:
            return {"name": game_status.team2Name, "team": "team2"}

    def get_current_red_team_info(self, game_code: str):
        """현재 레드 진영에 있는 팀 정보 반환"""
        game_status = self.game_status.get(game_code)
        if not game_status:
            return None
        
        if game_status.team1Side == "red":
            return {"name": game_status.team1Name, "team": "team1"}
        else:
            return {"name": game_status.team2Name, "team": "team2"}

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
            
            # 게임 결과 가져오기
            game_result = self.game_results.get(game_code)
            team1_score = game_result.team1Score if game_result else 0
            team2_score = game_result.team2Score if game_result else 0
            
            # 게임 결과 세부 정보 (각 세트별 데이터)
            results = game_result.results if game_result else []
            
            # 디버깅을 위한 로그
            print(f"get_game for {game_code}: Results count = {len(results)}")
            if results:
                for i, result in enumerate(results):
                    print(f"  Set {i+1}: {len(result)} phases, Winner: {result[21] if len(result) > 21 else 'None'}")
            
            # 게임 정보를 구성합니다
            game_info = {
                'code': game_code,
                'settings': {
                    'playerType': game_settings.playerType,
                    'matchFormat': game_settings.matchFormat,
                    'draftType': game_settings.draftType,  # 하드피어리스 모드 확인을 위한 드래프트 타입
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
                    'team1Name': game_status.team1Name,
                    'team2Name': game_status.team2Name,
                    'team1Side': game_status.team1Side,
                    'team2Side': game_status.team2Side,
                    'previousSetPicks': game_status.previousSetPicks or {},  # 하드피어리스를 위한 이전 세트 픽 정보
                    # 하위 호환성을 위한 블루/레드팀 이름 (현재 진영 기준)
                    'blueTeamName': game_status.team1Name if game_status.team1Side == "blue" else game_status.team2Name,
                    'redTeamName': game_status.team1Name if game_status.team1Side == "red" else game_status.team2Name,
                },
                'clients': clients,
                'team1Score': team1_score,
                'team2Score': team2_score,
                'results': results,  # 각 세트별 결과 데이터 추가
                # 하위 호환성을 위한 블루/레드 점수 (현재 진영 기준)
                'blueScore': team1_score if game_status.team1Side == "blue" else team2_score,
                'redScore': team1_score if game_status.team1Side == "red" else team2_score
            }
            
            print(f"Game info for {game_code}: {game_info}")
            return game_info
        except Exception as e:
            print(f"Error in get_game: {e}")
            raise
