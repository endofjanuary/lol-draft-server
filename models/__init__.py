from pydantic import BaseModel
from typing import List, Optional, Literal, Dict

class GameSetting(BaseModel):
    version: str
    draftType: Literal["tournament", "hardFearless", "softFearless"]
    playerType: Literal["single", "1v1"]
    matchFormat: Literal["bo1", "bo3", "bo5"]
    timeLimit: bool
    globalBans: Optional[List[str]] = []
    bannerImage: Optional[str] = None
    gameName: Optional[str] = "새로운 게임"

class Game(BaseModel):
    gameCode: str
    createdAt: int
    gameName: Optional[str] = "New Game"

class GameStatus(BaseModel):
    phase: int = 0
    team1Name: str = "Team 1"
    team2Name: str = "Team 2"
    lastUpdatedAt: int
    phaseData: List[str]
    setNumber: int = 1
    team1Side: str = "blue"    # Team 1의 현재 진영 (blue 또는 red)
    team2Side: str = "red"     # Team 2의 현재 진영 (red 또는 blue)
    previousSetPicks: Optional[Dict[str, List[str]]] = {}  # 하드피어리스를 위한 이전 세트 픽 정보

class SetResult(BaseModel):
    phaseData: List[str]
    team1Side: str  # "blue" or "red"
    team2Side: str  # "blue" or "red"
    winner: str     # "team1" or "team2"

class GameResult(BaseModel):
    team1Score: int = 0
    team2Score: int = 0
    results: List[SetResult] = []
    sideChoices: List[str] = []

class Client(dict):
    """클라이언트 정보를 저장하는 딕셔너리 클래스"""
    pass

__all__ = ['Game', 'GameSetting', 'GameStatus', 'GameResult', 'SetResult', 'Client']
