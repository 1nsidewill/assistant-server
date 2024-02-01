from fastapi import FastAPI
from app.config import Settings
from app.routers import agent_router
import uvicorn

app = FastAPI(title=Settings().app_name)
app.include_router(agent_router, prefix="/agent")