from fastapi import APIRouter, HTTPException
from models import Game, GameSetting
from services.game_service import GameService

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
