import os
import platform
from datetime import datetime
from fastapi import FastAPI
from routes import game_routes
from services.socket_service import SocketService
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="LoL Draft Server")

# Get allowed origins from environment variable
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins != "*":
    allowed_origins = allowed_origins.split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/ping")
async def ping():
    """Simple health check endpoint to verify server is responding"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": platform.python_version(),
        "message": "LoL Draft Server is running"
    }

# Include routers
app.include_router(game_routes.router)

# Setup Socket.IO at the root path
socket_service = SocketService()
socket_service.game_service = game_routes.game_service  # Link to the game service
app.mount("/", socket_service.setup())
