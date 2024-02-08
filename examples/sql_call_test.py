import json
 
from langchain_community.utilities.sql_database import (SQLDatabase)
 
from app.assistant.tools.sqltool import SQLCallTool
from app.assistant.tools.openapitool import (OpenAPITool, OpenAPISpec)
from app.assistant import get_chatllm
from app.crud.metadb import QueryMetaDB
from app.config import Settings
 
conf = Settings()
llm = get_chatllm(conf)
metadb = QueryMetaDB()
 
api_id = '1'
(system_id, api_spec) = metadb.get_api(api_id)
(system_type, system_spec) = metadb.get_system(system_id)
 
if system_type == "SQL":
    service: dict = json.loads(system_spec)
    server = service['servers'][0]
    from sqlalchemy import URL
    url_object = URL.create(
        server['dialet'],
        username=server['user'],
        password=server['password'],  # plain (unescaped) text
        host=server['host'],
        port=server['port'],
        database=server['name'],
    )
    datadb = SQLDatabase.from_uri(database_uri=url_object)
 
    sql = SQLCallTool.from_llm_and_spec(
        llm=llm,
        spec=api_spec,
        datadb=datadb,
    )
 
    result = sql.invoke(input={"schema":api_spec, "args":{"id":"1"}})
    print(result)
elif system_type == "REST":
    app_api_spec: dict = json.loads(system_spec)
    app_api_spec.update(dict(json.loads(api_spec)))
    path = list(app_api_spec['paths'].keys())[0]
    method = list(app_api_spec['paths'][path].keys())[0]
 
    tool = OpenAPITool.from_llm_and_method(
        llm=llm,
        path=path,
        method=method,
        spec=OpenAPISpec.from_spec_dict(app_api_spec),
    )
 
    result = tool.run("didim365.cc 등록 가능한 도메인을 알려 줘")
    print(result)