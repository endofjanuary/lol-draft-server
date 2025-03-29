import time
import secrets
from models import Game, GameSetting, GameStatus
from fastapi import Request

class GameService:
    def __init__(self):
        self.games = {}
        self.game_settings = {}
        self.game_status = {}
    
    async def create_game(self, setting: GameSetting, request: Request = None) -> Game:
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
                # Extract game name
                if "gameName" in raw_body:
                    game_name = raw_body["gameName"]
                
                # Extract team names
                if "teamNames" in raw_body and isinstance(raw_body["teamNames"], dict):
                    team_names = raw_body["teamNames"]
                    if "blue" in team_names:
                        blue_team_name = team_names["blue"]
                    if "red" in team_names:
                        red_team_name = team_names["red"]
                
                # Extract team names directly if specified
                if "blueTeamName" in raw_body:
                    blue_team_name = raw_body["blueTeamName"]
                if "redTeamName" in raw_body:
                    red_team_name = raw_body["redTeamName"]
                
                # Extract globalBans if specified
                if "globalBans" in raw_body and isinstance(raw_body["globalBans"], list):
                    setting.globalBans = raw_body["globalBans"]
                
                # Extract bannerImage if specified
                if "bannerImage" in raw_body and isinstance(raw_body["bannerImage"], str):
                    setting.bannerImage = raw_body["bannerImage"]
            except Exception as e:
                # Log error but continue with defaults
                print(f"Error extracting additional game data: {str(e)}")
        
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
            redTeamName=red_team_name
        )
        
        # Store in memory
        self.games[game_code] = game
        self.game_settings[game_code] = setting
        self.game_status[game_code] = status
        
        return game

    def get_game_info(self, game_code: str):
        if game_code not in self.games:
            raise ValueError(f"Game not found: {game_code}")
            
        return {
            "game": self.games[game_code],
            "settings": self.game_settings[game_code],
            "status": self.game_status[game_code]
        }
