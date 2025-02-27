import time
import secrets
from models import Game, GameSetting, GameStatus

class GameService:
    def __init__(self):
        self.games = {}
        self.game_settings = {}
        self.game_status = {}
    
    def create_game(self, setting: GameSetting) -> Game:
        # Generate unique game code
        while True:
            game_code = secrets.token_hex(4)
            if game_code not in self.games:
                break
        
        current_time = int(time.time() * 1000000)
        
        # Initialize game
        game = Game(
            gameCode=game_code,
            createdAt=current_time
        )
        
        # Initialize game status
        status = GameStatus(
            lastUpdatedAt=current_time,
            phaseData=[""] * 22
        )
        
        # Store in memory
        self.games[game_code] = game
        self.game_settings[game_code] = setting
        self.game_status[game_code] = status
        
        return game
