from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class GameSetting(BaseModel):
    version: str = "13.24.1"
    draftType: str = "tournament"
    playerType: str = "1v1"  # "single", "1v1", "5v5"
    matchFormat: str = "bo1"  # "bo1", "bo3", "bo5"
    timeLimit: bool = False
    globalBans: List[str] = []
    bannerImage: Optional[str] = None

class GameStatus(BaseModel):
    phase: int = 0
    phaseData: List[str] = []
    lastUpdatedAt: int = 0
    setNumber: int = 1
    blueTeamName: str = "Blue"
    redTeamName: str = "Red"
    blueScore: int = 0
    redScore: int = 0

class Game(BaseModel):
    gameCode: str
    createdAt: int
    gameName: str = "New Game"

class Client(dict):
    """클라이언트 정보를 저장하는 딕셔너리 클래스"""
    pass

class GameResult(BaseModel):
    """게임 결과를 저장하는 클래스"""
    blueScore: int = 0
    redScore: int = 0
    results: List[List[str]] = []

__all__ = ['Game', 'GameSetting', 'GameStatus', 'GameResult', 'Client']
