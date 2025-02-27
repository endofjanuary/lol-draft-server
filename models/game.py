from pydantic import BaseModel
from typing import Literal, List

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
    phaseData: List[str]
    setNumber: int = 1

class GameResult(BaseModel):
    blueScore: int = 0
    redScore: int = 0
    results: List[List[str]] = []
