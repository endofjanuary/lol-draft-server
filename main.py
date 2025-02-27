from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import time
import secrets

app = FastAPI(title="LoL Draft Server")

# Models
class GameSetting(BaseModel):
    version: str
    draftType: Literal["tournament", "hardFearless", "softFearless"]
    playerType: Literal["single", "1v1", "5v5"]
    matchFormat: Literal["bo1", "bo3", "bo5"]
    timeLimit: bool

class Game(BaseModel):
    gameCode: str
    createdAt: int

class GameStatus(BaseModel):
    phase: int = 0
    blueTeamName: str = "Blue"
    redTeamName: str = "Red"
    lastUpdatedAt: int
    phaseData: list[str]
    setNumber: int = 1

# In-memory storage
games = {}
game_settings = {}
game_status = {}

@app.post("/games", response_model=Game)
async def create_game(setting: GameSetting):
    try:
        # Generate unique 8-character hexadecimal game code
        while True:
            game_code = secrets.token_hex(4)  # 8 characters (4 bytes)
            if game_code not in games:
                break
        
        # Create timestamp
        current_time = int(time.time() * 1000000)  # microseconds
        
        # Initialize game
        game = Game(
            gameCode=game_code,
            createdAt=current_time
        )
        
        # Initialize game status
        status = GameStatus(
            lastUpdatedAt=current_time,
            phaseData=[""] * 22  # Initialize with 22 empty strings
        )
        
        # Store in memory
        games[game_code] = game
        game_settings[game_code] = setting
        game_status[game_code] = status
        
        return game
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create game: {str(e)}"
        )
