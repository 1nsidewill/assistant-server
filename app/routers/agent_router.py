from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings

router = APIRouter()

@router.get("/{query}")
async def get_agent_query(query: str):
    agent = create_assistant_agent(Settings())
    return agent.invoke({"query":query})