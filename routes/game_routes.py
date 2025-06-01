from fastapi import APIRouter, HTTPException, Request
from models import Game, GameSetting, GameStatus
from services.game_service import GameService
from pydantic import BaseModel
from typing import List, Optional, Literal

router = APIRouter()
game_service = GameService()

@router.post("/games")
async def create_game(setting: GameSetting, request: Request):
    """새로운 게임을 생성합니다."""
    try:
        # 요청 디버깅
        print(f"게임 생성 요청: {setting}")
        
        # 게임 생성
        game = await game_service.create_game(setting, request)
        
        # 생성된 게임 정보 출력
        print(f"게임 생성 성공: {game.gameCode}")
        
        return game
    except Exception as e:
        print(f"Error in create_game endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"게임 생성에 실패했습니다: {str(e)}")

class ClientInfo(BaseModel):
    nickname: str
    position: str
    isReady: bool = False  # Added isReady field with default value
    isHost: bool = False   # Added isHost field with default value

class GameClients(BaseModel):
    clients: List[ClientInfo]

class GameInfo(BaseModel):
    game: Game
    settings: GameSetting  # This already includes bannerImage
    status: GameStatus
    clients: List[ClientInfo] = []  # Added clients field with default empty list
    team1Score: int = 0  # 기존 blueScore 대신
    team2Score: int = 0  # 기존 redScore 대신
    bannerImage: Optional[str] = None  # Add explicit field for banner image

class SideChoiceRequest(BaseModel):
    choice: Literal["keep", "swap"]  # 진영 유지 또는 교체

@router.post("/games/{game_code}/choose-side")
async def choose_side(game_code: str, request: SideChoiceRequest):
    """패배한 팀이 진영을 선택합니다."""
    try:
        return await game_service.handle_side_choice(game_code, request.choice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/games/{game_code}")
async def get_game(game_code: str):
    """게임 정보를 반환합니다."""
    try:
        game_info = game_service.get_game(game_code)
        return game_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error in get_game endpoint: {e}")
        raise HTTPException(status_code=500, detail="게임 정보를 불러오는데 실패했습니다.")

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
