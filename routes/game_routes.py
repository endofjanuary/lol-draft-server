from fastapi import APIRouter, HTTPException
from models import Game, GameSetting, GameStatus
from services.game_service import GameService
from pydantic import BaseModel

router = APIRouter()
game_service = GameService()

@router.post("/games", response_model=Game)
async def create_game(setting: GameSetting):
    try:
        return game_service.create_game(setting)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create game: {str(e)}"
        )

class GameInfo(BaseModel):
    game: Game
    settings: GameSetting
    status: GameStatus

@router.get("/games/{game_code}", response_model=GameInfo)
async def get_game(game_code: str):
    try:
        return game_service.get_game_info(game_code)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game info: {str(e)}"
        )
