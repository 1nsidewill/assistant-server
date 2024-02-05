from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings
from app.crud import milvus, schema
from app.exceptions import *

router = APIRouter()

@router.post("/insert_row")
async def insert_row(item: schema.DomainItem):
    agent = create_assistant_agent(Settings())
    return agent.invoke({"query":""})

@router.post("/delete_row")
async def delete_row(item: schema.DomainItem):
    if True:
        print('')
    else:
        raise ItemNotFoundException()
    return ''

@router.post("/insert_documents")
async def insert_documents(item: schema.DomainItem):
    #connect milvus
    vector_db = milvus.connect_milvus()
    #recreate milvus collection(domain_desc)
    #recreate_milvus_collection()
    #get domain list in postgresql
    domain_list = milvus.check_domain_in_pg()

    #create domain document list
    documents = milvus.create_domain_document(domain_list)
    split_documents = milvus.split_documents(documents)

    print(split_documents)
    #insert_milvus(vector_db, documents)
    milvus.insert_milvus(vector_db, split_documents)

