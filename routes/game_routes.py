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

class ClientInfo(BaseModel):
    nickname: str
    position: str
    isReady: bool = False  # Added isReady field with default value
    isHost: bool = False   # Added isHost field with default value

class GameClients(BaseModel):
    clients: List[ClientInfo]

class GameInfo(BaseModel):
    game: Game
    settings: GameSetting
    status: GameStatus
    clients: List[ClientInfo] = []  # Added clients field with default empty list
    blueScore: int = 0  # Add blue team score field
    redScore: int = 0   # Add red team score field

@router.get("/games/{game_code}", response_model=GameInfo)
async def get_game(game_code: str):
    try:
        game_data = game_service.get_game_info(game_code)
        
        # Get client information for the game
        from main import socket_service
        game_clients = [
            client for client in socket_service.clients.values()
            if client.gameCode == game_code
        ]
        
        # Determine host (client with earliest joinedAt)
        host_client_id = None
        if game_clients:
            earliest_join_time = min(client.joinedAt for client in game_clients)
            host_client_id = next(
                client.socketId for client in game_clients 
                if client.joinedAt == earliest_join_time
            )
        
        # Create client list with host flag
        clients = [
            ClientInfo(
                nickname=client.nickname, 
                position=client.position, 
                isReady=client.isReady,
                isHost=(client.socketId == host_client_id)
            )
            for client in game_clients
        ]
        
        # Get team scores from game results if available
        blue_score, red_score = 0, 0
        if hasattr(game_service, 'game_results') and game_code in game_service.game_results:
            blue_score = game_service.game_results[game_code].blueScore
            red_score = game_service.game_results[game_code].redScore
        
        # Create GameInfo object properly from the dictionary
        game_info = GameInfo(
            game=game_data["game"],
            settings=game_data["settings"],
            status=game_data["status"],
            clients=clients,
            blueScore=blue_score,
            redScore=red_score
        )
        
        return game_info
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

@router.get("/games/{game_code}/clients", response_model=GameClients)
async def get_game_clients(game_code: str):
    try:
        # 게임 존재 여부 확인
        if game_code not in game_service.games:
            raise ValueError(f"Game not found: {game_code}")
            
        # socket_service에서 해당 게임에 연결된 클라이언트 조회
        from main import socket_service
        game_clients = [
            client for client in socket_service.clients.values()
            if client.gameCode == game_code
        ]
        
        # Determine host (client with earliest joinedAt)
        host_client_id = None
        if game_clients:
            earliest_join_time = min(client.joinedAt for client in game_clients)
            host_client_id = next(
                client.socketId for client in game_clients 
                if client.joinedAt == earliest_join_time
            )
        
        # Create client list with host flag
        clients = [
            ClientInfo(
                nickname=client.nickname, 
                position=client.position, 
                isReady=client.isReady,
                isHost=(client.socketId == host_client_id)
            )
            for client in game_clients
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
