import json

from langchain_community.chat_models import ChatHCX
# from langchain.globals import (set_debug)

from app.assistant.tools.openapitool import (OpenAPITool, OpenAPISpec)

# set_debug(True)

system_spec: str = '''{
    "openapi":"3.0.0",
    "info":{
        "title":"HyperClovaX-BOT",
        "description":"네임서버에 등록 가능한 도메인인지 확인해 볼 수 있는 API입니다.",
        "version":"0.0.1",
        "x-logo":{"url":"https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    },
    "servers": [ 
        { "url": "https://ai.didim365.com/hcxbot" } 
    ]
}'''
api_spec: str = '''{
    "paths": { 
        "/check_domain_exists": { 
            "get": { 
                "operationId": "check_domain_exists_check_domain_exists_get", 
                "parameters": [ 
                    { 
                        "name": "dom", 
                        "in": "query", 
                        "required": true, 
                        "schema": { 
                            "type": "string", 
                            "description": "등록 가능 여부를 체크할 도메인입니다. www. 를 제외한 도메인만 입력 가능합니다.", 
                            "title": "Dom" 
                        }, 
                        "description": "등록 가능 여부를 체크할 도메인입니다. www. 를 제외한 도메인만 입력 가능합니다."
                    }
                ], 
                "responses": { 
                    "200": { 
                        "description": "Successful Response", 
                        "content": { 
                            "application/json": { "schema": {} } 
                        } 
                    }
                }
            }
        }
    }
}'''
app_api_spec: dict = json.loads(system_spec)
app_api_spec.update(dict(json.loads(api_spec)))
path = list(app_api_spec['paths'].keys())[0]
method = list(app_api_spec['paths'][path].keys())[0]

llm = ChatHCX(
    api_base="https://clovastudio.stream.ntruss.com/testapp/v1", 
    clovastudio_api_key="NTA0MjU2MWZlZTcxNDJiY4jXFecF0MZvKTYhyWhTfQtGaumW+Uk4q+JxDEIjMiNLO34v3pE3xeKU4Jv+lojkoajJIv+Lz90M8HZpuXQCiqzQLqGV+QFg2n+/DGRN/cBqRNGtaWIPc6S8H+j9TCPg9t4LtqV0j0m9oQhoJ3teFF6NUMt9ypZiooDskBYvIEHB0L8dbqK6xPXyyR40nVW6MS9QVjiOINNzgYh0ci11rPI=", 
    apigw_api_key="OwD62s3yinzOaMBEZoS7vji97nb2tpg8irSOtJsx",
    model="HCX-003",
)
tool = OpenAPITool.from_llm_and_method(
    llm=llm,
    path=path,
    method=method,
    spec=OpenAPISpec.from_spec_dict(app_api_spec),
)

result = tool.run("didim365.cc 등록 가능한 도메인을 알려 줘")
print(result)
