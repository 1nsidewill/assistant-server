import json

from langchain.globals import (set_debug)
set_debug(True)

system_spec: str = '''{
    "servers": [ 
        {
            "name": "didimllm",
            "dialet": "postgresql",
            "driver": "pyscopg2",
            "user": "postgres",
            "password": "didim2401!",
            "host": "postgres-dev.didim365.store",
            "port": "5432"
        }
    ]
}'''
api_spec: str = '''{
    "sqls": { 
        "SELECT * FROM api_spec WHERE api_id = '{id}'": { 
            "parameters": [ 
                { 
                    "name": "id", 
                    "required": True, 
                    "schema": { 
                        "type": "string", 
                    }, 
                    "description": "api spec을 조회 할 PK"
                }
            ], 
        }
    }
}'''

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

from langchain.sql_database import SQLDatabase
db = SQLDatabase.from_uri(database_uri=url_object)

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.chat_models import ChatHCX
llm = ChatHCX(
    api_base="https://clovastudio.stream.ntruss.com/testapp/v1", 
    clovastudio_api_key="NTA0MjU2MWZlZTcxNDJiY4jXFecF0MZvKTYhyWhTfQtGaumW+Uk4q+JxDEIjMiNLO34v3pE3xeKU4Jv+lojkoajJIv+Lz90M8HZpuXQCiqzQLqGV+QFg2n+/DGRN/cBqRNGtaWIPc6S8H+j9TCPg9t4LtqV0j0m9oQhoJ3teFF6NUMt9ypZiooDskBYvIEHB0L8dbqK6xPXyyR40nVW6MS9QVjiOINNzgYh0ci11rPI=", 
    apigw_api_key="OwD62s3yinzOaMBEZoS7vji97nb2tpg8irSOtJsx",
    model="HCX-003",
)
# from langchain_community.chat_models.ollama import (ChatOllama)
# llm = ChatOllama()
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
toolkit= SQLDatabaseToolkit(llm=llm, db=db)

tools = toolkit.get_tools()
tool_names = [tool.name for tool in tools]
print(tool_names)

# sql_db_query_checker = tools[tool_names.index("sql_db_query_checker")]
# result = sql_db_query_checker.run(tool_input=api_spec)
template= """You are a helpful AI Assistant. Please provided SQL statement from json args based on the user's instructions.

SQL_SCHEMA: ```json
{schema}
```
ARGS: ```json
{args}
```

Example
-----
SQL_SCHEMA: ```json
{{"sqls":["SELECT * FROM foo WHERE bar > {{bar}}": {{"parameters":[{{"name":"bar"}}]}}]}}
```
ARGS: ```json
{{"bar": "1", "baz": {{"qux": "quux"}}}}
```
SQL_STATEMENT: ```text
SELECT * FROM foo WHERE bar > 1
```

The block must be no more than 1 line long, and all arguments must be valid. All string arguments must be wrapped in double quotes.
You MUST strictly comply to the types indicated by the provided schema, including all required args.

Begin
-----
SQL_STATEMENT:
"""
from langchain_core.prompts import (PromptTemplate)
prompt = PromptTemplate(
    template=template,
    input_variables=["schma", "instructions", "args"]
)

from langchain.chains import (LLMChain)
chain = LLMChain(
    prompt=prompt,
    llm=llm,
)

sql_input = chain.invoke(input={"schema":api_spec, "args":{"id":"1"}})
print(sql_input)

tool = tools[tool_names.index("sql_db_query")]
result = tool.run(sql_input['text'])

print(result)
