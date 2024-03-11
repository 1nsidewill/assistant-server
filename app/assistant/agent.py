from typing import (Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union,)
import json

from langchain_core.agents import (AgentAction, AgentFinish) #, AgentStep)
from langchain_core.callbacks import (BaseCallbackHandler)
from langchain_core.documents import (Document)
from langchain_core.language_models import (BaseLanguageModel)
# from langchain_core.embeddings import (Embeddings)
# from langchain_core.prompts import (ChatPromptTemplate, PromptTemplate)
# from langchain_core.vectorstores import (VectorStore)
from langchain_core.tools import (BaseTool)
from langchain_core.output_parsers import (StrOutputParser)
from langchain_community.utilities.sql_database import (SQLDatabase)

from langchain.agents.agent import (BaseSingleActionAgent) #, AgentExecutor)
# from langchain.chains import (LLMChain)
from langchain.agents.utils import (validate_tools_single_input)
from langchain.callbacks.manager import (Callbacks)
from app.crud.metadb import QueryMetaDB
from app.assistant.tools.openapitool import (OpenAPITool, OpenAPISpec)
from app.assistant.tools.sqltool import SQLCallTool
from app.assistant.templates import AgentTemplates
from app.assistant.sessionlog import RedisSessionLog

class AssistantAgent(BaseSingleActionAgent):
    """Agent powered by didm365."""

    llm: Optional[BaseLanguageModel] = None
    """llm model"""
    tools: Optional[Sequence[BaseTool]] = None
    allowed_tools: Optional[List[str]] = None
    """datadb"""
    datadb: Optional[SQLDatabase] = None
    """tools"""
    callbacks: Optional[List[BaseCallbackHandler]] = None
    """callbacks"""
    sessionlog: Optional[RedisSessionLog] = None
    """sessionlog"""
    _input_keys: List[str] = []
    """Input keys."""
    _outputs: List[Dict[str, Any]] = []
    """outputs"""
    _metadb: Optional[QueryMetaDB] = None
    # _metadb_uri: Optional[str] = None
    """query Database"""
    _response: dict[str, Any] = {}
    
    def dict(self, **kwargs: Any) -> Dict:
        """Return dictionary representation of agent."""
        _dict = super().dict()
        # del _dict["output_parser"]
        return _dict

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        """Validate that appropriate tools are passed in."""
        # super()._validate_tools(tools)
        validate_tools_single_input(cls.__name__, tools)
    
    def get_allowed_tools(self) -> Optional[List[str]]:
        return self.allowed_tools
    
    def _next(self, observation: Dict[str, Any], config: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
        query = observation['query']
        
        """Parse text into agent action/finish."""
        intermediate_steps = observation.pop("intermediate_steps", None)
        if len(intermediate_steps) == 0:
            # 1. 처음 들어올 때
            self._response.update({"query": query, "stage": "start"})
            return AgentAction(tool="domain_desc", tool_input=query, log="find domain from vectorstore(domain_desc)", kwargs=config)
        else:
            intermediate = intermediate_steps[-1]
            agent_action:AgentAction  = intermediate[0]
            # 2. domain 조회 후
            if agent_action.tool == "domain_desc":
                self._response['stage'] = 'check_domain'
                docs: List[Document] = intermediate[-1]
                if len(docs) > 0:
                    domain_id = docs[0].metadata['domain_id']
                    observation.update({"domain_id": domain_id})
                    self._response['domain_id'] = domain_id
                    return AgentAction(tool="api_desc", tool_input=observation, log="find api from vectorstore(api_spec)", kwargs=config)
                else:
                    return AgentFinish(return_values=self._response, log="cant find domain from vectorstore(domain_desc)")
            # 3. api_spec 조회 후
            elif agent_action.tool == "api_desc":
                self._response['stage'] = 'check_api'
                docs: List[Document] = intermediate[-1]
                if len(docs) > 0:
                    api_id = docs[0].metadata['api_id']
                    score = docs[0].metadata.get('score', 0)
                    self._response['api_id'] = api_id
                    self._response['score'] = score
                    
                    print("Executed API Calls are : ")
                    for doc in docs:
                        print("API ID with Score : " + str(doc.metadata['api_id']) + ", "+ str(doc.metadata.get('score', 0)))
                        
                    (api_spec, connect_type, connect_spec)= self.metadb.get_api(api_id)
                    
                    try:                                         
                        if connect_type == "REST":
                            app_api_spec: dict = json.loads(connect_spec)
                            app_api_spec.update(dict(json.loads(api_spec)))
                            path = list(app_api_spec['paths'].keys())[0]
                            method = list(app_api_spec['paths'][path].keys())[0]

                            self._response['stage'] = 'api_call'
                            
                            api_tool = OpenAPITool.from_llm_and_method(
                                llm=self.llm,
                                path=path,
                                method=method,
                                spec=OpenAPISpec.from_spec_dict(app_api_spec),
                            )
                            
                            result = api_tool.run(observation)
                            self._response['query_response'] = result
                            
                            return AgentFinish(return_values=self._response, log="agent end with api_call")
                        elif connect_type == "SQL":
                            self._response['stage'] = 'sql_call'
                            
                            service: dict = json.loads(connect_spec)
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
                                                        
                            sql = SQLCallTool.from_llm_and_spec(
                                llm=self.llm,
                                spec=api_spec,
                                datadb=self.datadb,
                            )
                        
                            self._response['query_response'] = result
                            
                            return AgentFinish(return_values=self._response, log="agent end with sql_call")
                    except Exception as e:
                        error_msg = "error handling api call : " + str(e) + " so instead find docs text from vectorstore(chunk_text)"
                        print(error_msg)
                        return AgentAction(tool="chunk_text", tool_input=observation, log=error_msg, kwargs=config)
                else:
                    return AgentAction(tool="chunk_text", tool_input=observation, log="find docs text from vectorstore(chunk_text)", kwargs=config)
            # 5. docs text 조회 후
            elif agent_action.tool == "chunk_text":
                self._response['stage'] = 'RAG'
                docs: List[Document] = intermediate[-1]
                if len(docs) > 0:
                    atmp = AgentTemplates('rag')
                    context = atmp.get_context_with_documents(docs)
                    self._response['file_ids'] = atmp.get_files_with_documents(docs)
                    self._response['chunk_ids'] = atmp.get_chunks_with_documents(docs)
                    self._response['scores'] = atmp.get_scores_with_documents(docs)
                    prompt = atmp.get_prompt()

                    chain = prompt | self.llm | StrOutputParser()
                    result = chain.invoke({"context":context, "question": query})
                    self._response['query_response'] = result

                    
                    return AgentFinish(return_values=self._response, log="agent end with docs text")
                else:
                    return AgentFinish(return_values=self._response, log="cant find data from vectorstore(api_desc or chunk_text)")
    
    async def _anext(self, observation: Dict[str, Any], config: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
        return self._next(observation, config)

    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True

    @property
    def return_values(self) -> List[str]:
        """Return values of the agent."""
        return self._outputs

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.
        Returns:
            List of input keys.
        """
        return self._input_keys

    @property
    def metadb(self) -> QueryMetaDB:
        if self.__class__._metadb == None:
            self.__class__._metadb = QueryMetaDB()
        return self.__class__._metadb

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLanguageModel,
        tools: Sequence[BaseTool],
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        sessionlog: Optional[RedisSessionLog] = None,
        **kwargs: Any,
    ) -> BaseSingleActionAgent:
        cls._validate_tools(tools)
        return cls(
            llm = llm,
            tools=tools,
            allowed_tools=[tool.name for tool in tools],
            callbacks=callbacks,
            sessionlog=sessionlog,
            **kwargs,
        )

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with the observations.
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        inputs = {**kwargs, **{"intermediate_steps": intermediate_steps}}
        output = self._next(inputs, config={"callbacks": callbacks or self.callbacks})
        return output

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        inputs = {**kwargs, **{"intermediate_steps": intermediate_steps}}
        output = await self._anext(inputs, config={"callbacks": callbacks or self.callbacks})
        return output