from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings
from app.crud import schema
from app.exceptions import *

router = APIRouter()

@router.post("/insert_row")
async def insert_row(item: schema.DomainItem):
    agent = create_assistant_agent(Settings())
    return agent.invoke({"query":""})

@router.post("delete_row")
async def delete_row(item: schema.DomainItem):
    if True:
        print('')
    else:
        raise ItemNotFoundException()
    return ''

@router
async def update_row(item: schema.DomainItem):
    return ''