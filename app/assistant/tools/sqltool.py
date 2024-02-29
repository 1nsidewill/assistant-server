from typing import (Any, Optional, Dict, Union, Tuple, List)

from langchain_core.language_models import (BaseLanguageModel)
from langchain_core.tools import (Tool)
from langchain.chains import (LLMChain)
from langchain_core.prompts import (PromptTemplate)
from langchain_community.utilities.sql_database import (SQLDatabase)
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

sql_template= """You are a helpful AI Assistant. Please provided SQL statement from json args based on the user's instructions.

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

class SQLCallTool():
    """SQL Call Tool."""

    def __init__(self, tool, sql_input):
        self.tool = tool  # Assuming 'tool' is an instance of another class or data structure
        self.sql_input = sql_input  # Assuming 'sql_input' is the output of LLMChain or similar
    # Example method to demonstrate usage
    def run(self):
        result = self.tool.run(self.sql_input['text'])

        return result
        
    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        print(args)
        print(kwargs)

    @classmethod
    def from_llm_and_spec(
        cls,
        llm: BaseLanguageModel,
        spec: str = None,
        datadb: Optional[SQLDatabase] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> "SQLCallTool":
        prompt = PromptTemplate(
            template=sql_template,
            input_variables=["schema", "instructions", "args"]
        )
        chain = LLMChain(
            prompt=prompt,
            llm=llm,
        )

        if datadb is None:
            from app.config import Settings
            conf = Settings()
            if conf.data_uri is None:
                raise ValueError("'data_uri' must be provided in .env.")
            datadb = SQLDatabase.from_uri(conf.data_uri)

        toolkit= SQLDatabaseToolkit(llm=llm, db=datadb)
        tools = toolkit.get_tools()
        tool_names = [tool.name for tool in tools]
        tool = tools[tool_names.index("sql_db_query")]
        
        sql_input = chain.invoke(input={"schema":spec, 
            "args":{"id":"1"}})
            
        return cls(
            tool=tool,
            sql_input=sql_input,
        )
        