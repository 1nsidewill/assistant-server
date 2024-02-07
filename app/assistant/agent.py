from typing import (Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union,)
import json

from langchain_core.agents import (AgentAction, AgentFinish, AgentStep)
from langchain_core.callbacks import (BaseCallbackHandler)
from langchain_core.documents import (Document)
from langchain_core.language_models import (BaseLanguageModel)
from langchain_core.embeddings import (Embeddings)
from langchain_core.prompts import (ChatPromptTemplate)
from langchain_core.vectorstores import (VectorStore)
from langchain_core.tools import (BaseTool)

from langchain.agents.agent import (BaseSingleActionAgent, AgentExecutor)
from langchain.chains import (LLMChain)
from langchain.agents.utils import (validate_tools_single_input)
from langchain.callbacks.manager import (Callbacks)
from app.crud.metadb import QueryMetaDB
from app.assistant.tools.openapitool import (OpenAPITool, OpenAPISpec)

class AssistantAgent(BaseSingleActionAgent):
    """Agent powered by didm365."""

    llm: Optional[BaseLanguageModel] = None
    """llm model"""
    tools: Optional[Sequence[BaseTool]] = None
    allowed_tools: Optional[List[str]] = None
    """tools"""
    callbacks: Optional[List[BaseCallbackHandler]] = None
    """callbacks"""
    _input_keys: List[str] = []
    """Input keys."""
    _outputs: List[Dict[str, Any]] = []
    """outputs"""
    _metadb: Optional[QueryMetaDB] = None
    # _metadb_uri: Optional[str] = None
    """query Database"""

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
            """Parse text into agent action/finish."""
            intermediate_steps = observation.pop("intermediate_steps", None)
            if len(intermediate_steps) == 0:
                # 1. 처음 들어올 때
                return AgentAction(tool="domain_desc", tool_input=observation, log="find domain from vectorstore(domain_desc)", kwargs=config)
            else:
                intermediate = intermediate_steps[-1]
                agent_action:AgentAction  = intermediate[0]
                # 2. domain 조회 후
                if agent_action.tool == "domain_desc":
                    docs: List[Document] = intermediate[-1]
                    if len(docs) > 0:
                        observation.update({"domain": docs[0].page_content})
                        return AgentAction(tool="api_desc", tool_input=observation, log="find api from vectorstore(api_spec)", kwargs=config)
                    else:
                        return AgentFinish(return_values={}, log="cant find domain from vectorstore(domain_desc)")
                # 3. api_spec 조회 후
                elif agent_action.tool == "api_desc":
                    docs: List[Document] = intermediate[-1]
                    if len(docs) > 0:
                        api_id = docs[0].metadata['api_id']
                        (system_id, api_spec)= self.metadb.get_api(api_id)
                        (connect_type, connect_spec)= self.metadb.get_system(system_id)
                        
                        app_api_spec: dict = json.loads(connect_spec)
                        app_api_spec.update(dict(json.loads(api_spec)))
                        path = list(app_api_spec['paths'].keys())[0]
                        method = list(app_api_spec['paths'][path].keys())[0]
                        
                        if connect_type == "REST":
                            api_tool = OpenAPITool.from_llm_and_method(
                                llm=self.llm,
                                path=path,
                                method=method,
                                spec=OpenAPISpec.from_spec_dict(app_api_spec),
                            )
                            
                            result = api_tool.run('')
                            
                            return AgentFinish(return_values=result, log="agent end with api")
                        elif connect_type == "SQL":
                            prompt_str = self.metadb.get_prompt(self.metadb.prompt['FILL_SQL_QUERTY'])
                            prompt = ChatPromptTemplate.from_template(prompt_str)

                            api_call = LLMChain(llm=self.llm, prompt=prompt).invoke(observation) # api spec -> SQL 준비

                            return AgentAction(tool="sql_db_query", tool_input=api_call, log="find data with query sql", kwargs=config)
                    else:
                        return AgentAction(tool="chunk_desc", tool_input=observation, log="find docs text from vectorstore(chunk_text)", kwargs=config)
                # 4. API call 후
                elif agent_action.tool == "request_get":
                    docs: List[Document] = intermediate[-1]
                    if len(docs) > 0:
                        observation.update({"api": docs[0].page_content})
                        result = LLMChain().invoke(input) # api result -> Call 준비
                        return AgentFinish(return_values=result, log="agent end with api")
                    else:
                        return AgentFinish(return_values={}, log="cant find data with api call")
                # 5. docs text 조회 후
                elif agent_action.tool == "chunk_text":
                    docs: List[Document] = intermediate[-1]
                    if len(docs) > 0:
                        observation.update({"api": docs[0].page_content})
                        result = LLMChain().invoke(input) # chunk text -> Call 준비
                        return AgentFinish(return_values=result, log="agent end with docs text")
                    else:
                        return AgentFinish(return_values={}, log="cant find data from vectorstore(api_desc or chunk_text)")

    
    async def _anext(self, observation: Dict[str, Any], config: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
            """Parse text into agent action/finish."""
            return AgentFinish({}, "self._outputs[-1]")

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
        **kwargs: Any,
    ) -> BaseSingleActionAgent:
        cls._validate_tools(tools)
        return cls(
            llm = llm,
            tools=tools,
            allowed_tools=[tool.name for tool in tools],
            callbacks=callbacks,
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