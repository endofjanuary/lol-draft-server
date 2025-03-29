from pydantic import BaseModel
from typing import Literal, List, Optional

class GameSetting(BaseModel):
    version: str
    draftType: Literal["tournament", "hardFearless", "softFearless"]
    playerType: Literal["single", "1v1", "5v5"]
    matchFormat: Literal["bo1", "bo3", "bo5"]
    timeLimit: bool
    globalBans: Optional[List[str]] = []  # Added globalBans field
    bannerImage: Optional[str] = None  # Added bannerImage field for base64-encoded image

class Game(BaseModel):
    gameCode: str
    createdAt: int
    gameName: Optional[str] = "New Game"  # Added gameName field

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
