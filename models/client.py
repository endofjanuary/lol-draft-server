from dataclasses import dataclass
from typing import Optional

@dataclass
class Client:
    socket_id: str
    game_code: str
    position: str
    joined_at: int
    nickname: str
    is_ready: bool = False
    is_host: bool = False
    selected_champion: Optional[str] = None
