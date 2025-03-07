from fastapi import APIRouter, HTTPException
from models import Game, GameSetting, GameStatus
from services.game_service import GameService
from pydantic import BaseModel
from typing import List

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

class ClientInfo(BaseModel):
    nickname: str
    position: str

class GameClients(BaseModel):
    clients: List[ClientInfo]

@router.get("/games/{game_code}/clients", response_model=GameClients)
async def get_game_clients(game_code: str):
    try:
        # 게임 존재 여부 확인
        if game_code not in game_service.games:
            raise ValueError(f"Game not found: {game_code}")
            
        # socket_service에서 해당 게임에 연결된 클라이언트 조회
        from main import socket_service
        clients = [
            ClientInfo(nickname=client.nickname, position=client.position)
            for client in socket_service.clients.values()
            if client.gameCode == game_code
        ]
        
        return GameClients(clients=clients)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game clients: {str(e)}"
        )
