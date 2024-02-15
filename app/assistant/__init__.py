from typing import (Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union,)

from langchain_core.tools import (BaseTool)
from langchain_core.callbacks import (BaseCallbackHandler)
from langchain_core.embeddings import (Embeddings)
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import BaseMessage

from langchain.agents.agent import (AgentExecutor)
from langchain.chains import ( StuffDocumentsChain, LLMChain, ConversationalRetrievalChain )
from langchain.memory import ConversationBufferMemory
from langchain.requests import (RequestsWrapper)
from langchain.tools.retriever import (create_retriever_tool)
from langchain.vectorstores.milvus import Milvus

from langchain_community.chat_models import ChatHCX
from langchain_community.embeddings import HCXEmbeddings
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.callbacks import HCXCallbackHandler
from langchain_community.tools.sql_database.tool import (QuerySQLDataBaseTool, InfoSQLDatabaseTool, ListSQLDatabaseTool, QuerySQLCheckerTool, )
from langchain_community.utilities.sql_database import (SQLDatabase)

from app.assistant.agent import AssistantAgent
from app.assistant.tools.openapitool import OpenAPITool
from app.assistant.tools.document_retriever_tool import create_retriever_tool as document_retriever_tool

from app.config import Settings

def get_memory(session_id: str, config: Settings):
    message_history = RedisChatMessageHistory(
        url=config.redis_url, 
        ttl=600,
        session_id=session_id,
    )
    memory = ConversationBufferMemory(
        memory_key="chat_history", chat_memory=message_history
    )

    return memory

_ROLE_MAP = {"human": "Human: ", "ai": "Assistant: "}
CHAT_TURN_TYPE = Union[str, Tuple[str, str], BaseMessage]
def _get_chat_history(chat_history: List[CHAT_TURN_TYPE]) -> str:
    buffer = ""
    for dialogue_turn in chat_history:
        if isinstance(dialogue_turn, str):
            buffer += "\n" + dialogue_turn
        elif isinstance(dialogue_turn, BaseMessage):
            role_prefix = _ROLE_MAP.get(dialogue_turn.type, f"{dialogue_turn.type}: ")
            buffer += f"\n{role_prefix}{dialogue_turn.content}"
        elif isinstance(dialogue_turn, tuple):
            human = "Human: " + dialogue_turn[0]
            ai = "Assistant: " + dialogue_turn[1]
            buffer += "\n" + "\n".join([human, ai])
        else:
            raise ValueError(
                f"Unsupported chat history format: {type(dialogue_turn)}."
                f" Full chat history: {chat_history} "
            )
    return buffer

def get_callback(config: Settings):
    if config._callback == None:
        config._callback = HCXCallbackHandler(
            config.callback_name,
            {"service.name": "langchain-hcx"}, 
            config.callback_url,
        )
    return config._callback

def get_retriever_tool(embeddings: Embeddings, collection_name: str, 
    config: Settings, threshold: float, partition_key="", top_k: int = 1):
    connection_args = {
        "host": config.milvus_host,
        "port": config.milvus_port,
        "user": config.milvus_user,
        "password": config.milvus_password,
        "db_name": config.milvus_db_name,
    }
    vectorstore = Milvus(
        connection_args = connection_args,
        embedding_function = (embeddings or get_embeddings(config)),
        collection_name = collection_name or config.milvus_collection,
        drop_old = False,
        # Add Partition key Field
        partition_key_field = partition_key if partition_key != "" else {}
    )
    
    return document_retriever_tool(
        vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={'k': top_k, 'score_threshold': threshold}
        ), 
        collection_name, 
        "Searches and returns from milvus collection " + collection_name
    )
    
def get_sql(database_uri: str):
    return SQLDatabase.from_uri(database_uri=database_uri, engine_args={"echo":False})

def get_chatllm(config: Settings):
    return ChatHCX(
        api_base=config.hcx_api_base, 
        clovastudio_api_key=config.hcx_clovastudio_api_key,
        apigw_api_key=config.hcx_apigw_api_key,
        callbacks=[get_callback(config)],
    )
    
def get_embeddings(config: Settings, max_tokens: int):
    return HCXEmbeddings(
        api_base=config.emb_api_base, 
        clovastudio_api_key=config.emb_clovastudio_api_key,
        apigw_api_key=config.emb_apigw_api_key,
        app_id=config.emb_app_id,
        callbacks=[get_callback(config)],
        max_tokens=max_tokens
    )
    
    

def create_assistant_agent(
    config: Settings,
    thresholds: dict[str, float | None],
    top_k: int = 1,
    max_tokens: int = 2048,
    verbose: bool = False,
    **kwargs: Any,
) -> AgentExecutor:
    llm = get_chatllm(config)

    callbacks = [get_callback(config)]

    requests_wrapper = RequestsWrapper()
    embeddings = get_embeddings(config, max_tokens)
    datadb = SQLDatabase.from_uri(database_uri=config.data_uri)
    tools = [
        QuerySQLDataBaseTool(db=datadb),
        get_retriever_tool(embeddings, "domain_desc", config, thresholds["domain_desc"], top_k=1),
        get_retriever_tool(embeddings, "api_desc", config, thresholds["api_desc"], "domain_id", top_k=2),
        get_retriever_tool(embeddings, "chunk_text", config, thresholds["chunk_text"], top_k=top_k),
    ]
    agent = AssistantAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        datadb=datadb,
        callbacks=callbacks,
        kwargs=kwargs,
    )
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        callbacks=callbacks,
        verbose=verbose,
        **(kwargs or {}),
    )

__all__=[
    "AssistentAgent",
    "create_assistent_agent",
]
