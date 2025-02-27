from fastapi import FastAPI
from routes import game_routes

app = FastAPI(title="LoL Draft Server")

# Include routers
app.include_router(game_routes.router)
