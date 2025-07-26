import os
import platform
from datetime import datetime
from fastapi import FastAPI, HTTPException
from routes import game_routes
from services.socket_service import SocketService
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="LoL Draft Server")

# CORS 설정 - Netlify 도메인과 로컬 개발 환경 허용
allowed_origins = [
    "https://lol-draft.netlify.app",
    "https://develop--lol-draft.netlify.app",
    "http://localhost:3000",
    "http://localhost:8000",
]

# 환경 변수에서 추가 origin 허용
additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS", "").split(",")
for origin in additional_origins:
    if origin.strip():
        allowed_origins.append(origin.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# 라우터 등록 - API 라우터는 /api 접두사로 등록하고, 기존 경로도 유지
app.include_router(game_routes.router)  # 기존 경로 유지 
app.include_router(game_routes.router, prefix="/api")  # /api 접두사 추가

# Socket.IO 서비스 설정
socket_service = SocketService()
game_routes.game_service.socket_service = socket_service
socket_service.game_service = game_routes.game_service

# Socket.IO 앱 마운트
app.mount("/", socket_service.setup())

# Health check endpoint
@app.get("/ping")
async def ping():
    """Simple health check endpoint to verify server is responding"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": platform.python_version(),
        "message": "LoL Draft Server is running",
        "allowed_origins": allowed_origins  # 허용된 Origin 목록 추가 (디버깅용)
    }

@app.get("/games/{game_code}")
async def get_game(game_code: str):
    """게임 정보를 반환합니다."""
    try:
        game_info = game_routes.game_service.get_game(game_code)
        return game_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error in get_game endpoint: {e}")
        raise HTTPException(status_code=500, detail="게임 정보를 불러오는데 실패했습니다.")
