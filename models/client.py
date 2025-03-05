from pydantic import BaseModel

class Client(BaseModel):
    socketId: str
    gameCode: str
    position: str
    joinedAt: int
    nickname: str
    isReady: bool = False  # Default to not ready
