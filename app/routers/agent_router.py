from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings

router = APIRouter()

@router.get("/{query}")
async def get_agent_query(query: str):
    """
        didim365.cc 등록 가능한 도메인을 알려 줘
    """
    agent = create_assistant_agent(Settings())
    return agent.invoke({"query":query})