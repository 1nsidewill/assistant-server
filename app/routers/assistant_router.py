from fastapi import APIRouter
from app.assistant import (create_assistant_agent, AgentExecutor)
from app.config import Settings
from app import schema
from app.exceptions import *
import asyncio
from starlette.concurrency import run_in_threadpool

router = APIRouter()

async def invoke_with_timeout(executer, query, timeout=20):
    try:
        response = await asyncio.wait_for(
            run_in_threadpool(executer.invoke, query),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        return None

@router.post("/assistant_query")
async def assistant_query(request: Request, item: schema.AssistantQueryItem):
    query = item.query
    print("Querying Assistant with user input : " + query) 
    print("Headers Info :")
    for header, value in request.headers.items():
        print(f"{header}: {value}")
        
    try:
        executer: AgentExecutor = await create_assistant_agent(
            Settings(),
            item.thresholds, 
            top_k=item.rag_top_k, 
            max_tokens=item.max_tokens,
        )
        
        response = await invoke_with_timeout(executer, {"query": query})

        if response is None:
            return JSONResponse(content={"detail": "Operation timed out"}, status_code=408)
        
        sessionid = request.cookies.get('sessionid', '')
        if sessionid:
            print("Session Id : " + sessionid)
            executer.agent.sessionlog.add_message(sessionid, response)

        if 'query_response' in response:
            return JSONResponse(content=response, status_code=200)
        else:
            return JSONResponse(content={"detail": "No response from query processing"}, status_code=500)

    except asyncio.TimeoutError:
        return JSONResponse(content={"detail": "Operation timed out (unexpected)"}, status_code=408)
    except Exception as e:
        print("Error Logging : " + str(e))
        detail_message = 'Internal Server Error: ' + str(e)
        return JSONResponse(content={"detail": detail_message}, status_code=500)