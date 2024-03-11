from langchain_core.prompts import (PromptTemplate, ChatPromptTemplate)
from langchain_core.documents import (Document)
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnableParallel, RunnablePassthrough

class AgentTemplates():
    def __init__(self, template_type):
        self.template_type = template_type
        
    def get_prompt(self):
        template = '' 
        if self.template_type == 'rag':
            prompt = ChatPromptTemplate.from_template(
                """아래의 context 내용을 바탕으로 사용자의 question에 답변해줘. 모르면 알지 못한다고 말해줘.:
                    {context}

                    Question: {question}
                """
            )
            
            return prompt
        elif self.template_type == 'sql':
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
        else:
            return ''
    
    def get_context_with_documents(self, documents: list):
        context = ''
        for index, document in enumerate(documents, start=1):
            context += f"{index}. {document.page_content}\n\n"
            
        return context
        
    def get_files_with_documents(self, documents: list[Document]):
        files = []
        for document in documents:
            files.append(document.metadata['file_id'])
            
        return files
    
    def get_chunks_with_documents(self, documents: list[Document]):
        chunks = []
        for document in documents:
            chunks.append(document.metadata['chunk_index'])
            
        return chunks
    
    def get_scores_with_documents(self, documents: list[Document]):
        scores = []
        for document in documents:
            scores.append(document.metadata.get('score', 0))
            
        return scores