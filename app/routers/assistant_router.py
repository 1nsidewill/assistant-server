from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings
from app import schema
from app.exceptions import *

router = APIRouter()

@router.post("/assistant_query")
async def assistant_query(item: schema.AssistantQueryItem):
    """
        didim365.cc 등록 가능한 도메인을 알려 줘
    """
    agent = create_assistant_agent(Settings(), item.thresholds, top_k=item.rag_top_k)
    query = item.query
    response = agent.invoke({"query":query})
    
    if 'query_response' in response:
        return JSONResponse(content=response, status_code=200)
    else:
        raise NothingToRespondException(response['stage'])