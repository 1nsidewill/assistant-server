from langchain_core.prompts import (PromptTemplate)

class AgentTemplates():
    def __init__(self, template_type):
        self.template_type = template_type
        
    def get_prompt(self):
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
        prompt = PromptTemplate(
            template=template,
            input_variables=["schema", "instructions", "args"]
        )
        
        return prompt