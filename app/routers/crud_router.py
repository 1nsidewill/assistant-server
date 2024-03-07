from fastapi import APIRouter
from app.assistant import create_assistant_agent
from app.config import Settings
from app.crud import milvus
from app.exceptions import *
from app import schema

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
    vector_db = milvus.connect_milvus("domain_desc")
    #recreate milvus collection(domain_desc)
    #recreate_milvus_collection()
    #get domain list in postgresql
    domain_list = milvus.check_domain_in_pg()

    #create domain document list
    documents = milvus.create_domain_document(domain_list)
    split_documents = milvus.split_documents(documents)

    ids = milvus.create_ids(split_documents, "domain_id")
    print(split_documents)
    #insert_milvus(vector_db, documents)
    milvus.insert_milvus(vector_db, split_documents, ids)

@router.post("/insert_documents_into_api_desc")
async def insert_documents_into_api_desc(item: schema.DomainItem):
    #connect milvus
    vector_db = milvus.connect_milvus("api_desc")
    #recreate milvus collection(domain_desc)
    #recreate_milvus_collection()
    #get domain list in postgresql
    domain_list = milvus.check_domain_in_pg()

    #create domain document list
    documents = milvus.create_domain_document(domain_list)
    split_documents = milvus.split_documents(documents)

    print(split_documents)
    ids = milvus.create_ids(split_documents, "api_id")
    #insert_milvus(vector_db, documents)
    milvus.insert_milvus(vector_db, split_documents, ids)

@router.get("/recreate_collection")
async def recreate_collection(collection_name):
    try:
        milvus.recreate_milvus_collection(collection_name)
    except Exception as e:
        raise HTTPException(500)
    
@router.post("/insert_test_data")
async def insert_test_data(item: schema.ApiDescItem):
    # test
    """
    {
        "collection_name": "api_desc",
        "text": "사원의 연차 (휴가) 상세 정보를 확인 할 수 있다. 날짜를 입력받는다",
        "api_id": 4,
        "domain_id": 9
    }
    """
    #connect milvus
    try:
        vector_db = milvus.connect_milvus(item.collection_name)
        documents = milvus.insert_test_data(item)
        ids = milvus.create_ids(documents, "api_id")
        milvus.insert_milvus(vector_db, documents, ids)
        print('Done')
    except Exception as e:
        raise HTTPException(500)