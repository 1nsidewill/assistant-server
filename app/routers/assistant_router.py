from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings
from app import schema
from app.exceptions import *

router = APIRouter()

@router.post("/assistant_query")
async def assistant_query(item: schema.AssistantQueryItem):
    """
        1. Executing API
        query : didim365.cc 등록 가능한 도메인을 알려 줘
        2. Executing SQL call
        query : 데이터베이스에서 도메인 확인하는 Spec을 조회해줘
        
        사용자의 질문을 답변하는 Assistant입니다.
        
        1. 우선 도메인이 등록되어 있는지 확인합니다.
        2. 도메인이 있다면 API / SQL SPEC 이 db에 존재하는지 확인합니다.
        3. 조회된 call type 에 맞게 execution 이 실행됩니다.
        4. 위 프로세스를 위한 spec이 조회되지 않는다면, RAG를 조회합니다.
        5. 최종 Response를 사용자에게 전달합니다.
    """
    agent = create_assistant_agent(Settings(), item.thresholds, 
        top_k=item.rag_top_k, max_tokens=item.max_tokens
    )
    
    query = item.query
    response = agent.invoke({"query":query})
    
    if 'query_response' in response:
        return JSONResponse(content=response, status_code=200)
    else:
        raise NothingToRespondException(response['stage'])