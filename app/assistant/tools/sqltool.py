from typing import (Any, Optional, Dict, Union, Tuple, List)

from langchain_core.language_models import (BaseLanguageModel)
from langchain_core.tools import (Tool)
from langchain.chains import (LLMChain)
from langchain_core.prompts import (PromptTemplate)
from langchain_community.utilities.sql_database import (SQLDatabase)

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

class SQLCallTool(Tool):
    """SQL Call Tool."""

    datadb: SQLDatabase
    chain: LLMChain

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
        spec: Dict[str, Any],
        datadb: Optional[SQLDatabase] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> "SQLCallTool":
        prompt = PromptTemplate(
            template=sql_template,
            input_variables=["schma", "instructions", "args"]
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

        title = spec.info.title
        expanded_name = (
            f'{title.replace(" ", "_")}'
        )
        description = (
            f"I'm an AI from {title}. Instruct what you want,"
            " and I'll assist via an SQL with description:"
            f" {chain.description}"
        )
        return cls(
            datadb=datadb,
            chain=chain,
            name=expanded_name,
            description=description
        )