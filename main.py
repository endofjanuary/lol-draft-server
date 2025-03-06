from fastapi import FastAPI
from routes import game_routes
from services.socket_service import SocketService
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="LoL Draft Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game_routes.router)

# Setup Socket.IO at the root path
socket_service = SocketService()
socket_service.game_service = game_routes.game_service  # Link to the game service
app.mount("/", socket_service.setup())
